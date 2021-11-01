import datetime
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class LeavePolicy(models.TransientModel):
    _name = 'leave.policy'
    _description = "Leave Policy Report Wizard"

    def get_year(self):
        return [(num, num) for num in range((datetime.date.today().year - 10), (datetime.date.today().year + 1))]

    year = fields.Selection(lambda self: self.get_year(), default=datetime.date.today().year)
    start_date = fields.Date(compute='_compute_start_end_date')
    end_date = fields.Date(compute='_compute_start_end_date')

    @api.depends('year')
    def _compute_start_end_date(self):
        for record in self:
            record.start_date = datetime.date(int(record.year), 1, 1)
            record.end_date = datetime.date(int(record.year), 12, 31)

    def generate_accrual_report(self):
        if len(self._context['active_ids']) > 1:
            raise ValidationError('Please Select only one policy to print report for it')
        policy = self._context.get('active_ids') and \
                   self.env['leave.accrual.policy'].browse(self._context['active_ids']) or []
        datas = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'year': self.year,
        }
        return self.env.ref('hr_leave_accrual.leave_accrual_xlsx').report_action(policy, data=datas)
