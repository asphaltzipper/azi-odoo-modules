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

    @api.constrains('employee_id', 'policy_id', 'start_date', 'end_date')
    def _constrain_dates(self):
        overlapping = self.search([
            ('employee_id', '=', self.employee_id),
            ('policy_id', '=', self.policy_id),
            '|',
            ('start_date', '>=', self.start_date),
            ('start_date', '<=', self.end_date),
            '&',
            ('end_date', '>=', self.start_date),
            ('end_date', '<=', self.end_date),
        ])
        if overlapping:
            raise ValidationError("The dates for this policy overlap another.")
