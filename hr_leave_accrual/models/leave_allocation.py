from odoo import models, fields, api


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
    allocation_type = fields.Selection([('add', 'Add'), ('remove', 'Remove')],
                                       'Allocation Type', default='add')
    used_amount = fields.Float('Used Amount')

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record.type_id.name + '-' + str(record.start_date)
            result.append((record.id, name))
        return result
