import datetime
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class LeaveAllocationEmployee(models.TransientModel):
    _name = 'leave.allocation.employee'
    _description = 'Generate Report per Employee'

    def get_years(self):
        return [(num, num) for num in range((datetime.date.today().year - 10), (datetime.date.today().year + 2))]

    year = fields.Selection(lambda self: self.get_years(), 'Year', default=datetime.date.today().year)
    employee_id = fields.Many2one('hr.employee', 'Employee')

    def get_employee_allocations(self):
        start_date = datetime.date(int(self.year), 1, 1)
        end_date = datetime.date(int(self.year), 12, 31)
        allocation_ids = self.env['leave.allocation'].search([('start_date', '>=', start_date),
                                                              ('start_date', '<=', end_date),
                                                              ('employee_id', '=', self.employee_id.id)])
        if not allocation_ids:
            raise ValidationError('No record found for this employee')
        action = self.env.ref('hr_leave_accrual.action_leave_allocation_tree').read()[0]
        action.update(domain=[('id', 'in', allocation_ids.ids)], context=dict(search_default_group_alloc_type=1))
        return action
