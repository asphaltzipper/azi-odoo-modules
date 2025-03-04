import datetime
from odoo import models, fields, api


class Employee(models.Model):
    _inherit = 'hr.employee'
    _sql_constraints = [('swipeclock_ref_uniq', 'unique (swipeclock_ref)', "SwipeClock reference must be unique."), ]

    swipeclock_ref = fields.Char(
        string="SwipeClock Ref",
        help="Employee ID from SwipeClock",
    )
