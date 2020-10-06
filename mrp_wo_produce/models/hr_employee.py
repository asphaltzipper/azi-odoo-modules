from odoo import models, fields


class Employee(models.Model):
    _inherit = 'hr.employee'

    barcode = fields.Char(copy=False)
