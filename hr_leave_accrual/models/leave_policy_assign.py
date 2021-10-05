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

    start_date = fields.Date(
        string="Start Date",
        required=True,
    )

    end_date = fields.Date(
        string="End Date",
    )
    policy_line_ids = fields.One2many('leave.policy.assign.line', 'policy_assign_id', 'Policy Lines')

    @api.constrains('employee_id', 'policy_id', 'start_date', 'end_date')
    def _constrain_dates(self):
        overlapping = self.search([
            ('employee_id', '=', self.employee_id.id),
            ('policy_id', '=', self.policy_id.id),
            '|',
            ('start_date', '>=', self.start_date),
            ('start_date', '<=', self.end_date),
            '&',
            ('end_date', '>=', self.start_date),
            ('end_date', '<=', self.end_date),
        ])
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

    def generate_policy_line(self, start_date, end_date, increment_date, half_month=False):
        allocation_ids = []
        beginning_year = start_date
        start_year = start_date.year
        while start_date <= end_date:
            if half_month:
                if start_date.day == 1:
                    end_date_period = datetime.date(start_date.year, start_date.month, 15)
                if start_date.day == 16:
                    calendar_month = calendar.monthrange(start_date.year, start_date.month)
                    end_date_period = datetime.date(start_date.year, start_date.month, calendar_month[1])
            else:
                end_date_period = start_date + increment_date
            allocation = self.env['leave.allocation'].create({'allocation_type': 'add',
                                                              'employee_id': self.employee_id.id,
                                                              'alloc_amount': self.policy_id.rate,
                                                              'type_id': self.policy_id.type_id.id,
                                                              'start_date': start_date,
                                                              'end_date': end_date_period})
            allocation_ids.append(allocation.id)
            if half_month:
                if end_date_period.day == 15:
                    start_date = end_date_period + datetime.timedelta(days=1)
                else:
                    end_of_next_month = start_date + relativedelta(months=1)
                    start_date = datetime.date(end_of_next_month.year, end_of_next_month.month, 1)
            else:
                start_date = end_date_period + datetime.timedelta(days=1)
        self.env['leave.policy.assign.line'].create({'year': start_year,
                                                     'start_date': beginning_year,
                                                     'end_date': end_date,
                                                     'leave_allocation_ids': [(6, 0, allocation_ids)],
                                                     'policy_assign_id': self.id})

    def generate_allocation(self):
        for record in self:
            start_year = record.start_date.year
            start_date = record.start_date
            period_unit = record.policy_id.period_unit
            period_duration = record.policy_id.period_duration
            if period_unit == 'week':
                increment_date = relativedelta(weeks=period_duration)
            elif period_unit == 'half_month':
                increment_date = relativedelta(days=15*period_duration)
            else:
                increment_date = relativedelta(months=period_duration)
            policy_line = record.policy_line_ids.filtered(lambda l: l.year == start_year)
            end_date = self.get_end_date(start_year, record.end_date)
            half_month = period_unit == 'half_month' and period_duration == 1
            if policy_line and record.policy_line_ids[0].year+1 <= datetime.date.today().year:
                start_date = record.policy_line_ids[0].leave_allocation_ids.sorted(
                    lambda p: p.end_date, reverse=True)[0].end_date
                start_year = start_date.year
                start_date = half_month and datetime.date(start_date.year+1, 1, 1) or start_date
                end_date = self.get_end_date(start_date.year, record.end_date)
                record.generate_policy_line(start_date, end_date, increment_date, half_month)
            elif not policy_line and start_date.year <= datetime.date.today().year:
                record.generate_policy_line(start_date, end_date, increment_date, half_month)

    @api.model
    def create_allocation_per_policy(self):
        for policy_assign in self.search([]):
            policy_assign.generate_allocation()


class LeavePolicyAssignLine(models.Model):
    _name = 'leave.policy.assign.line'
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
