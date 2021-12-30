from odoo import models, fields


class LeaveType(models.Model):
    _name = 'leave.type'
    _description = 'Leave Type'

    name = fields.Char(
        string='Name',
        required=True,
    )

    leave_unit = fields.Selection(
        selection=[
            ('hour', 'Hour'),
            ('day', 'Day'),
        ],
        string="Unit",
    )

    limit_rollover = fields.Boolean(
        string="Limit Rollover",
        required=True,
        default=False,
        help="Has a limit on year-end balance rollover",
    )

    rollover_limit = fields.Float(
        string="Rollover Limit",
        required=True,
        help="Allow this amount of leave time to roll over at year-end",
    )
