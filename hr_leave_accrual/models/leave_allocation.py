from odoo import models, fields, api
from odoo.exceptions import ValidationError


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
    allocation_type = fields.Selection(
        selection=[('accrued', 'Accrued'), ('adjusted', 'Adjusted'), ('consumed', 'Consumed')],
        string='Allocation Type',
        default='accrued',
        required=True,
    )
    balance = fields.Float('Balance', compute='_compute_balance', store=True)
    used_amount = fields.Float('Used Amount')

    @api.depends('allocation_type', 'alloc_amount')
    def _compute_balance(self):
        for record in self:
            record.balance = record.allocation_type == 'consumed' and -record.alloc_amount or record.alloc_amount

    @api.constrains('allocation_type', 'alloc_amount')
    def _check_amount_per_type(self):
        for record in self:
            if record.allocation_type == 'accrued' and not self.env.user.has_group('hr.group_hr_manager'):
                raise ValidationError('You are not allowed to create or edit accrual allocation, please '
                                      'contact HR manager')
            if record.allocation_type == 'consumed' and record.alloc_amount < 0:
                raise ValidationError('Consumed allocation should have positive values')

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record.type_id.name + '-' + str(record.start_date)
            result.append((record.id, name))
        return result
