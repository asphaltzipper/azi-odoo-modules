import datetime
import calendar
from dateutil.relativedelta import relativedelta

from odoo import models
from odoo.exceptions import ValidationError


class LeaveAllocationsYearlyReport(models.AbstractModel):
    _name = 'report.hr_leave_accrual.leave_allocations_yearly_report'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Leave Allocations Annual Report'

    def generate_xlsx_report(self, workbook, data, allocations):
        """ This report assumes all allocations have the same rate unit, period duration, and period unit

        :param workbook: provided by report_xlsx module
        :param data: dict containing the following fields
            * start_date
            * end_date
            * year
            * rate_unit
            * period_duration
            * period_unit
        :param allocations: record set of leave allocations
        :return: None
        """

        if not data.get('start_date') or not data.get('end_date'):
            return
        start_date = datetime.datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
        year = int(data.get('year'))
        rate_unit = data.get('rate_unit')
        period_duration = data.get('period_duration')
        period_unit = data.get('period_unit')

        # set up the two header rows
        header = workbook.add_format({'bold': True, 'align': 'center'})
        header_date = workbook.add_format({'bold': True, 'align': 'center', 'num_format': 'yyyy-mm-dd'})
        row_date = workbook.add_format({'num_format': 'yyyy-mm-dd'})

        start_date_period = start_date
        sheet = workbook.add_worksheet('Sheet1')
        sheet.set_column(0, 4, 20)
        sheet.write(0, 0, "Employee", header)
        sheet.write(0, 1, "Hire Date", header)
        sheet.write(0, 2, "Years Of Service", header)
        sheet.write(0, 3, "Type", header)
        sheet.merge_range(0, 4, 0, 5, "Previous", header)
        sheet.write(1, 4, "Lost", header)
        sheet.write(1, 5, "Rollover", header)
        period_dates = []
        if period_unit == 'week':
            increment_date = relativedelta(weeks=period_duration)
        elif period_unit == 'half_month':
            increment_date = relativedelta(days=15 * period_duration)
        else:
            increment_date = relativedelta(months=period_duration)
        half_month = period_unit == 'half_month' and period_duration == 1
        i = 6
        while start_date_period < end_date:
            if half_month and start_date_period.day == 1:
                end_date_period = start_date_period + relativedelta(days=14)
            elif half_month and start_date_period.day == 16:
                if start_date_period.month == 12:
                    temp_date = datetime.date(start_date_period.year+1, 1, 1)
                else:
                    temp_date = datetime.date(start_date_period.year, start_date_period.month+1, 1)
                end_date_period = temp_date - relativedelta(days=1)
            else:
                end_date_period = start_date_period + increment_date

            sheet.merge_range(0, i, 0, i + 3, end_date_period, header_date)
            sheet.write(1, i, "Accrued", header)
            sheet.write(1, i + 1, "Used", header)
            sheet.write(1, i + 2, "Adjust", header)
            sheet.write(1, i + 3, "Balance", header)
            period_dates.append(end_date_period)

            start_date_period = end_date_period + datetime.timedelta(days=1)
            i += 4
            if i > 256:
                raise ValidationError("Exceeded xlsx column limit")

        # get all employees with leave allocations for the year
        employees = allocations.mapped('employee_id')

        # get rollover allocations
        raw_rollover = self.env['leave.allocation'].read_group(
            domain=[
                ('start_date', '>=', start_date),
                ('end_date', '<=', end_date),
                ('allocation_type', '=', 'rollover'),
            ],
            fields=['employee_id', 'type_id', 'alloc_amount'],
            groupby=['employee_id', 'type_id'],
            orderby='employee_id, type_id',
            lazy=False,
        )
        if raw_rollover:
            rollover = {(x['employee_id'][0], x['type_id'][0]): x['alloc_amount'] for x in raw_rollover}
        else:
            rollover = {}

        # get lost allocations
        lost_start_date = start_date - relativedelta(years=1)
        lost_end_date = end_date - relativedelta(years=1)
        raw_lost = self.env['leave.allocation'].read_group(
            domain=[
                ('start_date', '>=', lost_start_date),
                ('end_date', '<=', lost_end_date),
                ('allocation_type', '=', 'lost'),
            ],
            fields=['employee_id', 'type_id', 'alloc_amount'],
            groupby=['employee_id', 'type_id'],
            orderby='employee_id, type_id',
            lazy=False,
        )
        if raw_lost:
            lost = {(x['employee_id'][0], x['type_id'][0]): x['alloc_amount'] for x in raw_lost}
        else:
            lost = {}

        # get accrued, used, adjust, by period
        period_start_date = start_date
        period_allocations = {}
        starting_rate = {}
        for period_end_date in period_dates:
            raw = self.env['leave.allocation'].read_group(
                domain=[
                    ('start_date', '>=', period_start_date),
                    ('end_date', '<=', period_end_date),
                    ('allocation_type', 'in', ['accrued', 'consumed', 'adjusted']),
                ],
                fields=['employee_id', 'type_id', 'allocation_type', 'alloc_amount'],
                groupby=['employee_id', 'type_id', 'allocation_type'],
                orderby='employee_id, type_id, allocation_type',
                lazy=False,
            )
            period_allocations[period_end_date] = {
                (x['employee_id'][0], x['type_id'][0], x['allocation_type']): x['alloc_amount'] for x in raw}
            # get starting accrual rate
            for alloc in raw:
                if alloc['allocation_type'] == 'accrued' and \
                        alloc['alloc_amount'] and \
                        not starting_rate.get(alloc['employee_id']):
                    starting_rate[alloc['employee_id']] = alloc['alloc_amount']
            period_start_date = period_end_date + datetime.timedelta(days=1)

        # fill the report body with data
        count = 2  # cell refs are zero-based, so this is starting at row 3
        for emp in employees:
            for leave_type in allocations.mapped('type_id'):
                hire_date = emp.hire_date or ""
                sheet.write(count, 0, emp.name, header)
                sheet.write(count, 1, hire_date, row_date)
                no_of_years = 0
                if hire_date:
                    no_of_years = relativedelta(datetime.date.today(), emp.hire_date)
                    no_of_years = no_of_years.years + (no_of_years.months / 12)
                sheet.write(count, 2, round(no_of_years, 1))
                sheet.write(count, 3, leave_type.name)
                sheet.write(count, 4, round(lost.get((emp.id, leave_type.id), 0), 2))
                sheet.write(count, 5, round(rollover.get((emp.id, leave_type.id), 0), 2))

                running_balance = rollover.get((emp.id, leave_type.id), 0)
                col = 6
                for period_date in period_dates:
                    accrued = period_allocations.get(period_date).get((emp.id, leave_type.id, 'accrued'), 0)
                    used = period_allocations.get(period_date).get((emp.id, leave_type.id, 'consumed'), 0)
                    adjusted = period_allocations.get(period_date).get((emp.id, leave_type.id, 'adjusted'), 0)
                    running_balance += accrued + used + adjusted
                    sheet.write(count, col, round(accrued, 2))
                    sheet.write(count, col + 1, round(used, 2))
                    sheet.write(count, col + 2, round(adjusted, 2))
                    sheet.write(count, col + 3, round(running_balance, 2))
                    col += 4
                count += 1
