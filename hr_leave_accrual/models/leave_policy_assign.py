import datetime
import calendar
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class LeavePolicyAssign(models.Model):
    _name = 'leave.policy.assign'
    _description = 'Leave Policy Assign'

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
    )
    start_date = fields.Date(
        string="Start Date",
        required=True,
    )
    end_date = fields.Date(
        string="End Date",
    )
    policy_line_ids = fields.One2many(
        comodel_name='leave.policy.assign.line',
        inverse_name='policy_assign_id',
        string='Policy Lines',
    )

    @api.constrains('employee_id', 'policy_id', 'start_date', 'end_date')
    def _constrain_dates(self):
        # don't allow policies for the same leave type to have overlapping date ranges
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

    @staticmethod
    def get_end_date(year, end_date):
        end_of_year = datetime.date(year, 12, 31)
        if end_date and end_date > end_of_year:
            return end_of_year
        if not end_date:
            return end_of_year
        return end_date

    def generate_policy_line(self, start_date, end_date, period_unit, period_duration):
        allocation_ids = []
        if period_unit == 'week':
            # start on the monday before
            start_date_period = start_date - datetime.timedelta(days=start_date.weekday() % 7)
            # end on the sunday after
            end_date_period = start_date_period + datetime.timedelta(days=6)
        elif period_unit == 'month':
            # start on the first of the given month
            start_date_period = datetime.date(start_date.year, start_date.month, 1)
            # end on the last day of the given month
            end_date_period = start_date_period + relativedelta(months=1) - datetime.timedelta(days=1)
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
                # end_date_period = datetime.date(start_date.year, start_date.month, 1) + \
                #                   relativedelta(months=1) - datetime.timedelta(days=1)
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
                    # end_date_period = datetime.date(start_date_period.year, start_date_period.month, 1) + \
                    #                   relativedelta(months=1) - datetime.timedelta(days=1)
                    last_day = calendar.monthrange(start_date_period.year, start_date_period.month)[1]
                    end_date_period = datetime.date(start_date_period.year, start_date_period.month, last_day)
        vals = {
            'year': start_date.year,
            'start_date': start_date,
            'end_date': end_date,
            'leave_allocation_ids': [(6, 0, allocation_ids)],
            'policy_assign_id': self.id,
        }
        self.env['leave.policy.assign.line'].create(vals)

    def generate_allocation(self):
        for record in self:
            start_year = record.start_date.year
            start_date = record.start_date
            period_unit = record.policy_id.period_unit
            period_duration = record.policy_id.period_duration
            policy_line = record.policy_line_ids.filtered(lambda l: l.year == start_year)
            end_date = self.get_end_date(start_year, record.end_date)
            half_month = period_unit == 'half_month' and period_duration == 1
            if policy_line and record.policy_line_ids[0].year+1 <= datetime.date.today().year:
                # a line for the starting year of this policy assignment already exists
                # but a line for the current year does not exist
                # set the start date for the new line to the end date of the latest allocation, plus one
                # this will break if the users has deleted all allocations, and wants to regenerate them
                start_date = record.policy_line_ids[0].leave_allocation_ids.sorted(
                    lambda p: p.end_date, reverse=True)[0].end_date + datetime.timedelta(days=1)
                # if half_month, set start_date to the first day of the year after the latest allocation end date
                # this can skip periods if the latest allocation doesn't end on 12/31
                start_date = half_month and datetime.date(start_date.year+1, 1, 1) or start_date
                end_date = self.get_end_date(start_date.year, record.end_date)
                record.generate_policy_line(start_date, end_date, period_unit, period_duration)
            elif not policy_line and start_date.year <= datetime.date.today().year:
                record.generate_policy_line(start_date, end_date, period_unit, period_duration)

    @api.model
    def create_allocation_per_policy(self):
        for policy_assign in self.search([]):
            policy_assign.generate_allocation()


class LeavePolicyAssignLine(models.Model):
    _name = 'leave.policy.assign.line'
    _description = "Leave Policy Assignment Detail Line"
    _order = 'year DESC'

    year = fields.Integer('Year')
    year_char = fields.Char('Year', compute='_compute_year', store=True)
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    balance = fields.Float('Opening Balance')
    adjust = fields.Float('Adjust')
    leave_allocation_ids = fields.Many2many('leave.allocation', string='Accrual Allocated')
    policy_assign_id = fields.Many2one('leave.policy.assign', 'Employee Policy')

    @api.depends('year')
    def _compute_year(self):
        for record in self:
            record.year_char = str(record.year)
