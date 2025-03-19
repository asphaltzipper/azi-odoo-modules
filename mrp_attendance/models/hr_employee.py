import datetime
from odoo import models, fields, api


class Employee(models.Model):
    _inherit = 'hr.employee'

    workcenter_distribution_ids = fields.One2many(
        comodel_name="employee.workcenter.distribution",
        inverse_name="employee_id",
        string="Workcenter Distributions",
    )

    current_attendance_workcenter_dist = fields.Integer(
        string="WC Dist",
        compute="_compute_current_attendance_workcenter_dist",
    )

    def _compute_current_attendance_workcenter_dist(self):
        for rec in self:
            rec.current_attendance_workcenter_dist = (
                rec.sudo().workcenter_distribution_ids
                and rec.sudo().workcenter_distribution_ids[-1].total_distribution
                or 0
            )
