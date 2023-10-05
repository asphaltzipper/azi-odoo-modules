from odoo import models, fields, api
from odoo.exceptions import ValidationError


class LeaveAllocation(models.Model):
    _name = 'leave.allocation'
    _description = 'Leave Allocation'
    _order = 'employee_id, type_id, start_date, allocation_type'

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
        string="Allocation Unit",
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
        selection=[
            ('accrued', 'Accrued'),
            ('adjusted', 'Adjusted'),
            ('consumed', 'Consumed'),
            ('rollover', 'Rollover'),
            ('lost', 'Lost'),
        ],
        string='Allocation Type',
        default='accrued',
        required=True,
        help=""
             "Accrued: Leave time accruals by period."
             "Adjusted: Manual adjustments to leave time."
             "Consumed: Leave time taken by the employee."
             "Rollover: Balance rolled over from the previous year.\n"
             "Lost: Leave time lost to rollover limit from previous year balance.",
    )

    @api.constrains('allocation_type', 'alloc_amount')
    def _check_amount_per_type(self):
        for record in self:
            if record.allocation_type == 'accrued' and record.alloc_amount <= 0:
                raise ValidationError('Accruing must be positive')
            if record.allocation_type == 'consumed' and record.alloc_amount >= 0:
                raise ValidationError('Consuming must be negative')
            if record.allocation_type == 'lost' and record.alloc_amount >= 0:
                raise ValidationError('Losing must be negative')

            # TODO: this appears to serve no purpose - remove it
            if record.allocation_type == 'accrued' and not self.env.user.has_group('hr.group_hr_manager'):
                raise ValidationError('You are not allowed to create or edit accrual allocation, please '
                                      'contact HR manager')

    def name_get(self):
        result = []
        for record in self:
            name = record.type_id.name + '-' + str(record.start_date)
            result.append((record.id, name))
        return result
