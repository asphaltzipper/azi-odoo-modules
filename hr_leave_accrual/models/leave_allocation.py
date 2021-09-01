from odoo import models, fields


class LeaveAllocation(models.Model):
    _name = 'leave.allocation'
    _description = 'Leave Allocation'

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string="Employee",
        required=True,
        ondelete='cascade',
    )

    type_id = fields.Many2one(
        comodel_name='leave.type',
        string="Leave Type",
        required=True,
    )

    alloc_amount = fields.Float(
        string="Allocation Amount",
        required=True,
    )

    alloc_unit = fields.Selection(
        related='type_id.leave_unit',
        strirg="Allocation Unit",
        readonly=True,
    )

    start_date = fields.Date(
        string="Start Date",
        required=True,
    )

    end_date = fields.Date(
        string="End Date",
        required=True,
    )
