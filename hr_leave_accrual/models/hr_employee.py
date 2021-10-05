from odoo import models, fields, api


class Employee(models.Model):
    _inherit = 'hr.employee'

    leave_avail_ids = fields.One2many(
        comodel_name='leave.accrual.avail',
        inverse_name='employee_id',
        string='Available Leave',
    )

    leave_accrual_allocated_ids = fields.One2many('leave.accrual.allocated', 'employee_id', 'Leave Allocations')
    hire_date = fields.Date('Hiring Date')
