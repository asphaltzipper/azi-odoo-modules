import datetime
from odoo import models, fields, api


class Employee(models.Model):
    _inherit = 'hr.employee'

    leave_policy_ids = fields.One2many(
        comodel_name='leave.policy.assign',
        inverse_name='employee_id',
        string="Leave Policies",
    )

    leave_summary_ids = fields.One2many(
        comodel_name='leave.allocation.summary',
        inverse_name='employee_id',
        string='Leave Summary',
    )

    hire_date = fields.Date(
        string='Hiring Date',
    )
