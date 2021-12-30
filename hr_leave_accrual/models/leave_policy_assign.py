import datetime
import calendar
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class LeavePolicyAssign(models.Model):
    _name = 'leave.policy.assign'
    _description = 'Leave Policy Assign'
    _order = 'type_id, start_date'

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string="Employee",
        required=True,
        ondelete='cascade',
    )
    policy_id = fields.Many2one(
        comodel_name='leave.accrual.policy',
        string="Policy",
        required=True,
        ondelete='cascade',
    )
    type_id = fields.Many2one(
        related='policy_id.type_id',
        string='Type',
        readonly=True,
        store=True,
    )
    start_date = fields.Date(
        string="Start Date",
        required=True,
    )
    end_date = fields.Date(
        string="End Date",
    )

    @api.constrains('employee_id', 'policy_id', 'start_date', 'end_date')
    def _constrain_dates(self):
        # don't allow policies for the same leave type to have overlapping date ranges
        # TODO: check for policies starting/ending in same period, but not overlapping
        # policies should end on the last day of a period, and start on the first
        # http://mysirg.org/convert-infix-to-prefix-notation
        # infix notation: a&b&c&((d&e)|(f&g)|(h&i))
        # prefix notation: &&&abc||&de&fg&hi
        # since & is the default operator, simplify: abc||&de&fg&hi
        end_date = self.end_date or datetime.date.today() + relativedelta(years=100)
        dom = [
            ('id', '!=', self.id),
            ('employee_id', '=', self.employee_id.id),
            ('type_id', '=', self.policy_id.type_id.id),
            '|',
            '|',
            '|',
            '&',
            # others with start_date bracketed by this start/end
            ('start_date', '>=', self.start_date),
            ('start_date', '<=', end_date),
            '&',
            # others with end_date bracketed by this start/end
            ('end_date', '>=', self.start_date),
            ('end_date', '<=', end_date),
            '&',
            # others open ended and starting before this ends
            ('end_date', '=', False),
            ('start_date', '<=', end_date),
            '&',
            # others completely containing this range
            ('end_date', '>=', end_date),
            ('start_date', '<=', self.start_date),
        ]
        overlapping = self.search(dom)
        if overlapping:
            raise ValidationError("The dates for this policy overlap another.")

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record.employee_id.name + ' - ' + record.policy_id.name
            result.append((record.id, name))
        return result

    def generate_accruals(self, year):
        # This method does not check for duplicate accrual entries.
        # You should perform your own check before calling this method.
        default_start_date = datetime.date(int(year), 1, 1)
        default_end_date = datetime.date(int(year), 12, 31)
        for record in self:
            if record.start_date > default_end_date or (record.end_date and record.end_date < default_start_date):
                # skip assigned policies not applicable in this year
                continue
            start_date = default_start_date
            if record.start_date > default_start_date:
                start_date = record.start_date
            end_date = default_end_date
            if record.end_date and record.end_date < default_end_date:
                end_date = record.end_date
            period_unit = record.policy_id.period_unit
            period_duration = record.policy_id.period_duration
            record.generate_accrual_lines(start_date, end_date, period_unit, period_duration)

    def generate_accrual_lines(self, start_date, end_date, period_unit, period_duration):
        allocation_ids = []
        if period_unit == 'week':
            # start on the monday before
            start_date_period = start_date - datetime.timedelta(days=start_date.weekday() % 7)
            # end on the sunday after
            end_date_period = start_date_period + datetime.timedelta(days=6 + 7*period_duration)
        elif period_unit == 'month':
            # start on the first of the given month
            start_date_period = datetime.date(start_date.year, start_date.month, 1)
            # end on the last day of the given month
            end_date_period = start_date_period + relativedelta(months=period_duration) - datetime.timedelta(days=1)
        elif period_unit == 'half_month':
            if start_date.day < 16:
                # start on the first of the given month
                start_date_period = datetime.date(start_date.year, start_date.month, 1)
                # end on the 15 of the given month
                end_date_period = datetime.date(start_date.year, start_date.month, 15)
            else:
                # start on the 16th of the given month
                start_date_period = datetime.date(start_date.year, start_date.month, 16)
                # end on the last day of the given month
                last_day = calendar.monthrange(start_date_period.year, start_date_period.month)[1]
                end_date_period = datetime.date(start_date.year, start_date.month, last_day)
        else:
            raise ValidationError("Unknown period unit: %s" % period_unit)
        # we do nothing in the case where a policy is assigned for less than a whole period
        while end_date_period <= end_date:
            vals = {
                'allocation_type': 'accrued',
                'employee_id': self.employee_id.id,
                'alloc_amount': self.policy_id.rate,
                'type_id': self.policy_id.type_id.id,
                'start_date': start_date_period,
                'end_date': end_date_period,
            }
            allocation = self.env['leave.allocation'].create(vals)
            allocation_ids.append(allocation.id)
            start_date_period = end_date_period + datetime.timedelta(days=1)
            if period_unit == 'week':
                end_date_period = start_date_period + datetime.timedelta(days=6)
            elif period_unit == 'month':
                end_date_period = start_date_period + relativedelta(months=1) - datetime.timedelta(days=1)
            elif period_unit == 'half_month':
                if start_date_period.day < 16:
                    # end on the 15 of the given month
                    end_date_period = start_date_period + datetime.timedelta(days=14)
                else:
                    # end on the last day of the given month
                    last_day = calendar.monthrange(start_date_period.year, start_date_period.month)[1]
                    end_date_period = datetime.date(start_date_period.year, start_date_period.month, last_day)
