import requests
import json
import re
import base64
from urllib.parse import quote, quote_plus
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, UTC, timedelta
from dateutil.relativedelta import relativedelta
import jwt


# assume 2 pay periods per month, spanning from the 1st to the 15th and from the
# 16th to the last day of the month

card_number_re = re.compile(r"^\d{8}$")

class SwipeclockAccount(models.Model):
    _name = 'swipeclock.account'
    _description = "Swipeclock account info"

    name = fields.Char(
        string="Account Name",
        required=True,
    )
    site_id = fields.Char(
        string="Site ID",
        required=True,
    )
    user_secret = fields.Char(
        string="API Secret Key",
        required=True,
    )
    api_url = fields.Char(
        string="API URL",
        required=True,
    )
    auth_url = fields.Char(
        string="Authorization URL",
        required=True,
    )
    employee_group = fields.Char(
        string="Employee Group",
    )
    audit_buffer_days = fields.Integer(
        string="Audit Buffer Days",
        required=True,
        help="Don't import the pay period until this many days after the end of the pay period",
    )
    minimum_begin_date = fields.Date(
        string="Minimum Begin Date",
        required=True,
        help="Don't import clock punches for pay periods beginning prior to this date",
    )
    last_begin_date = fields.Date(
        string="Latest Begin Date",
        help="Beginning date of the most recently imported pay period \n"
             "Must be either the 1st or the 16th of the month \n"
             "We only support two pay periods per month",
    )
    last_import_date = fields.Datetime(
        string="Last Import Date",
    )
    last_success = fields.Boolean(
        string="Success",
        required=True,
        default=False,
        help="Latest import attempt was successful",
    )
    log_ids = fields.One2many(
        comodel_name='swipeclock.log',
        inverse_name="account_id",
        string="Import Log",
    )

    def _get_token(self):
        unix_timestamp = (
            datetime.now(UTC)
            + timedelta(minutes=3)
            - datetime(1970, 1, 1, tzinfo=UTC)
        ).total_seconds()
        header_data = {
            "typ": "JWT",
            "alg": "HS256"
        }
        payload_data = {
            "iss": self.site_id,
            "sub": "client",
            "exp": int(unix_timestamp),
            "product": "twpclient",
            "siteInfo": {
                "type": "id",
                "id": self.site_id
            }
        }
        originating_token = jwt.encode(
            payload=payload_data,
            headers=header_data,
            key=self.user_secret,
            algorithm='HS256',
        )
        headers = {
            'content-type': 'application/json',
            'authorization': "Bearer " + originating_token,
        }
        response = requests.post(
            url=self.auth_url,
            # url=self.api_url + "/" + "AuthenticationService/oauth2/usertoken",
            headers=headers,
        )
        if response.status_code != 201:
            self.env['swipeclock.log'].log_entry({
                "account_id": self.id,
                "message": "Failed to get auth token from swipeclock",
                "details": f"status_code = {response.status_code}\n"
                           f"reason = {response.reason}",
            })
            raise UserError(f"Failed to get auth token from swipeclock")
        try:
            data = json.loads(response.text)
        except Exception as e:
            self.env['swipeclock.log'].log_entry({
                "account_id": self.id,
                "message": "Failed to convert employees JSON response",
                "details": f"exception = {e}",
            })
            raise UserError(f"Failed to convert auth token JSON response: {e}")
        auth_token = data.get("token")
        return auth_token

    def get_employees(self, token, employee_codes=False):
        # get Odoo employees by swipeclock ref
        domain = [('swipeclock_ref', '!=', False)]
        if employee_codes:
            domain.append(('swipeclock_ref', 'in', employee_codes))
        odoo_employees = self.env['hr.employee'].search(domain)
        employees_by_ref = {x.swipeclock_ref: x for x in odoo_employees}

        # get SwipeClock employees
        headers = {
            'content-type': 'application/json',
            'authorization': "Bearer " + token,
        }
        params = {
            'site': self.site_id,
            'showCurrency': False,
            'onlyActive': False,
            'showGroups': False,
            'showAnnouncements': False,  # the default is not specified in the API docs
        }
        if self.employee_group:
            params['filterByGroup'] = self.employee_group
        if employee_codes:
            params['ids'] = employee_codes
            params['idType'] = 'EmployeeCode'

        response = requests.get(
            url=f"{self.api_url}/api/{self.site_id}/employees",
            headers=headers,
            params=params,
        )
        if response.status_code != 200:
            self.env['swipeclock.log'].log_entry({
                "account_id": self.id,
                "message": "Failed to get employees from swipeclock",
                "details": f"status_code = {response.status_code}\n"
                           f"reason = {response.reason}",
            })
            raise UserError(f"Failed to get employees from swipeclock")
        try:
            data = json.loads(response.text)
        except Exception as e:
            self.env['swipeclock.log'].log_entry({
                "account_id": self.id,
                "message": "Failed to convert employees JSON response",
                "details": f"exception = {e}",
            })
            raise UserError(f"Failed to convert JSON response: {e}")
        swipeclock_employees = data["Results"]

        # check for unknown swipeclock employees
        sw_employee_codes = [x['EmployeeCode'] for x in swipeclock_employees]
        new_employee_codes = set(sw_employee_codes) - set(employees_by_ref.keys())
        if new_employee_codes:
            employee_infos = []
            for emp in swipeclock_employees:
                if emp["EmployeeCode"] in new_employee_codes:
                    if not any([card_number_re.match(x.get("Id")) for x in emp.get("Identifiers", [])]):
                        continue
                    employee_infos.append(f"{emp['FirstName']} {emp['LastName']} ({emp['EmployeeCode']})")
            message = _(
                f"Received %s unrecognized employee(s):\n%s",
                len(employee_infos),
                "\n".join(employee_infos),
            )
            self.env['swipeclock.log'].log_entry({
                "account_id": self.id,
                "message": "Received unrecognized employee(s)",
                "details": message,
            })
            # raise UserError(message)

        return employees_by_ref

    def get_timecards(self, period_begin_date, employee_codes, token):
        headers = {
            'content-type': 'application/json',
            'authorization': "Bearer " + token,
        }
        params = {
            'site': self.site_id,
            'idType': 'EmployeeCode',
            'periodDate': period_begin_date.strftime("%Y-%m-%d"),
            'ids': ','.join(employee_codes),
        }
        response = requests.get(
            url=f"{self.api_url}/api/{self.site_id}/timecards",
            headers=headers,
            params=params,
        )
        if response.status_code != 200:
            self.env['swipeclock.log'].log_entry({
                "account_id": self.id,
                "begin_date": period_begin_date,
                "message": "Failed to get timecards from swipeclock",
                "details": f"status_code = {response.status_code}\n"
                           f"reason = {response.reason}",
            })
            raise UserError(f"Failed to get timecards from swipeclock")
        try:
            data = json.loads(response.text)
        except Exception as e:
            self.env['swipeclock.log'].log_entry({
                "account_id": self.id,
                "begin_date": period_begin_date,
                "message": "Failed to convert timecards JSON response",
                "details": f"exception = {e}",
            })
            raise UserError(f"Failed to convert JSON response: {e}")
        return data

    def action_import(self):
        self.ensure_one()

        self.last_import_date = fields.Datetime.now()

        attendance = self.env['hr.attendance']

        token = self._get_token()
        employees = self.get_employees(token)

        # beginning date of initial period to import
        if self.last_begin_date:
            # get the beginning date of the next pay period
            if self.last_begin_date.day < 16:
                # the 16th of the same month
                initial_begin_date = self.last_begin_date.replace(day=16)
            else:
                # first day of the next month
                initial_begin_date = self.last_begin_date.replace(day=1) + relativedelta(months=1)
        else:
            initial_begin_date = self.minimum_begin_date

        # beginning date of final period to import
        # i.e. the beginning date of the most recently completed pay period
        if datetime.today().day > self.audit_buffer_days + 15:
            # first day of this month
            final_begin_date = date.today().replace(day=1)
        elif datetime.today().day > self.audit_buffer_days:
            # the 16th of last month
            final_begin_date = date.today().replace(day=15) - relativedelta(months=1)
        else:
            # first day of last month
            final_begin_date = date.today().replace(day=1) - relativedelta(months=1)

        if self.last_begin_date and self.last_begin_date >= initial_begin_date:
            message = _(
                f"You have already imported timecards through the period beginning %s",
                self.last_begin_date.strftime("%Y-%m-%d"),
            )
            self.env['swipeclock.log'].log_entry({
                "account_id": self.id,
                "begin_date": initial_begin_date,
                "message": "You have already imported timecards through the latest",
                "details": message,
            })
            raise UserError(message)

        if final_begin_date < initial_begin_date:
            message = _(
                f"The next period to import is not yet completed (beginning %s)",
                initial_begin_date.strftime("%Y-%m-%d"),
            )
            self.env['swipeclock.log'].log_entry({
                "account_id": self.id,
                "begin_date": initial_begin_date,
                "message": "The next period to import is not yet completed",
                "details": message,
            })
            raise UserError(message)

        # check for pre-existing punches
        employee_ids = [x.id for x in employees.values()]
        dom = [
            ("employee_id", "in", employee_ids),
            ("check_in", ">", initial_begin_date),
        ]
        existing_count = self.env['hr.attendance'].search_count(dom)
        if existing_count:
            message = _(
                f"There are already attendance punches in the period beginning %s\n"
                "Delete those, and try again, or set the Minimum Date later.",
                initial_begin_date.strftime("%Y-%m-%d"),
            )
            self.env['swipeclock.log'].log_entry({
                "account_id": self.id,
                "begin_date": initial_begin_date,
                "message": "There are already attendance punches in the period",
                "details": message,
            })
            raise UserError(message)

        punched_employees = {}
        period_dates_log = []
        missing_employees = []
        missing_punches = []
        current_begin_date = initial_begin_date
        while current_begin_date <= final_begin_date:
            # get timecard data from swipeclock
            data = self.get_timecards(
                period_begin_date=current_begin_date,
                employee_codes=list(employees.keys()),
                token=token,
            )

            # create punches
            for card in data['TimeCards']:
                employee = employees.get(card['Employee']['EmployeeCode'])
                if not employee:
                    missing_employees.append(
                        f"{card['Employee']['FirstName']} "
                        f"{card['Employee']['LastName']} "
                        f"({card['Employee']['EmployeeCode']})"
                    )
                    continue
                for punch_date in card['Dates']:
                    for punch_line in punch_date['Lines']:
                        in_str = punch_line['InUTC']
                        out_str = punch_line['OutUTC']
                        break_str = punch_line['BreakSeconds']

                        if not in_str:
                            continue
                        if not out_str:
                            message = _(
                                "Found a missing out punch for %s at %s",
                                employee.name,
                                in_str,
                            )
                            self.env['swipeclock.log'].log_entry({
                                "account_id": self.id,
                                "begin_date": initial_begin_date,
                                "message": message,
                            })
                            raise ValidationError(message)
                        in_time = datetime.strptime(in_str, "%Y-%m-%dT%H:%M:%SZ")
                        in_utc = in_time.replace(tzinfo=UTC)
                        out_time = datetime.strptime(out_str, "%Y-%m-%dT%H:%M:%SZ")
                        out_utc = out_time.replace(tzinfo=UTC)
                        break_seconds = break_str and float(break_str) or 0.0

                        attendance.create({
                            "employee_id": employee.id,
                            "check_in": in_utc.strftime("%Y-%m-%d %H:%M:%S"),
                            "check_out": out_utc.strftime("%Y-%m-%d %H:%M:%S"),
                            "break_seconds": break_seconds,
                        })

                        if punched_employees.get(employee.id):
                            punched_employees[employee.id] += 1
                        else:
                            punched_employees[employee.id] = 1

            # increment to the beginning date of the next pay period
            if current_begin_date.day < 16:
                period_dates_log.append(
                    current_begin_date.strftime("%Y-%m-%d")
                    + " - "
                    + current_begin_date.replace(day=15).strftime("%Y-%m-%d")
                )
                # the 16th of the same month
                current_begin_date = current_begin_date.replace(day=16)
            else:
                period_dates_log.append(
                    current_begin_date.strftime("%Y-%m-%d")
                    + " - "
                    + (
                            current_begin_date.replace(day=1)
                            + relativedelta(months=1)
                            - relativedelta(days=1)
                    ).strftime("%Y-%m-%d")
                )
                # first day of the next month
                current_begin_date = current_begin_date.replace(day=1) + relativedelta(months=1)

        if missing_employees:
            message = _(
                "Found unknown employees with punches:\n%s",
                "\n".join(missing_employees),
            )
            self.env['swipeclock.log'].log_entry({
                "account_id": self.id,
                "begin_date": initial_begin_date,
                "message": "Found unknown employees",
                "details": message,
            })
            raise ValidationError(message)

        self.last_begin_date = current_begin_date
        self.last_success = True

        punch_count = sum(punched_employees.values())
        self.env['swipeclock.log'].log_entry({
            "account_id": self.id,
            "success": True,
            "begin_date": initial_begin_date,
            "employee_count": len(punched_employees.keys()),
            "punch_count": punch_count,
            "message": "Timecard import completed successfully",
            "details": "Imported timecards for periods:\n%s" % "\n".join(period_dates_log)
        })
