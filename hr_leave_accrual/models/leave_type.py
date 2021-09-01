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
        string="Unit"
    )
