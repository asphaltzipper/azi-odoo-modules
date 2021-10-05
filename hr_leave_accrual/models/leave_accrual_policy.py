from odoo import models, fields, api


class LeaveAccrualPolicy(models.Model):
    _name = 'leave.accrual.policy'
    _description = 'Leave Accrual Policy'

    name = fields.Char(
        string='Name',
        required=True,
    )

    type_id = fields.Many2one(
        comodel_name='leave.type',
        string="Leave Type",
        required=True,
    )

    rate = fields.Float(
        string='Accrual Rate',
        help="Amount to accrue per period",
    )

    rate_unit = fields.Selection(
        related='type_id.leave_unit',
        strirg="Accrual Unit",
        readonly=True,
    )

    period_duration = fields.Integer(
        string='Period Duration',
        help="Duration of accrual period",
    )

    period_unit = fields.Selection(
        selection=[
            ('week', 'Week'),
            ('month', 'Month'),
            ('half_month', 'Half-Month'),
        ],
        string='Period Unit',
        help="Units of accrual period",
    )
    policy_assign_ids = fields.One2many('leave.policy.assign', 'policy_id', 'Assigned Policies')
    policy_count = fields.Integer('Policy Counts', compute='_compute_policy_count')

    @api.depends('policy_assign_ids')
    def _compute_policy_count(self):
        for record in self:
            record.policy_count = len(record.policy_assign_ids)
