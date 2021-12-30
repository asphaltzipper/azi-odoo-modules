import datetime
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class WizardLeaveAllocationsYearlyReport(models.TransientModel):
    _name = 'wizard.leave.allocations.yearly.report'
    _description = "Leave Allocations Yearly Report Wizard"

    def get_years(self):
        return [(num, num) for num in range((datetime.date.today().year - 10), (datetime.date.today().year + 2))]

    year = fields.Selection(
        selection=lambda self: self.get_years(),
        string="Year",
        required="True",
        default=datetime.date.today().year,
    )
    start_date = fields.Date(compute='_compute_start_end_date')
    end_date = fields.Date(compute='_compute_start_end_date')

    @api.depends('year')
    def _compute_start_end_date(self):
        for record in self:
            record.start_date = datetime.date(int(record.year), 1, 1)
            record.end_date = datetime.date(int(record.year), 12, 31)

    def generate_allocation_report(self):
        # the report contains data for all allocations in the given year
        # all policies must have the same rate unit, period duration, and period unit
        # TODO: get period info from user, rather than policies
        if not self.year:
            raise ValidationError("A year must be specified")
        if self._context.get('active_model', '') == 'leave.accrual.policy' and self._context.get('active_ids'):
            policies = self.env['leave.accrual.policy'].browse(self._context['active_ids'])
        else:
            policies = self.env['leave.accrual.policy'].search([])
        rate_unit = policies[0].type_id.leave_unit
        period_duration = policies[0].period_duration
        period_unit = policies[0].period_unit
        for policy in policies:
            if policy.type_id.leave_unit != rate_unit or \
                    policy.period_duration != period_duration or \
                    policy.period_unit != period_unit:
                raise ValidationError('Please Select only policies with the same rate unit, period duration, '
                                      'and period unit')
        types = policies.mapped('type_id')
        allocations = self.env['leave.allocation'].search([
            ('type_id', 'in', types.ids),
            ('start_date', '>=', self.start_date),
            ('end_date', '<=', self.end_date),
        ])
        datas = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'year': self.year,
            'rate_unit': rate_unit,
            'period_duration': period_duration,
            'period_unit': period_unit,
        }
        return self.env.ref('hr_leave_accrual.leave_allocations_yearly_xlsx').report_action(
            data=datas, docids=allocations)
