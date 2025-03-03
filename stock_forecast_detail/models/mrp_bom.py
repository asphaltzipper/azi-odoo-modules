from odoo import fields, models, api, _


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    def get_operations_recursion(self):
        return self.env['operations.recursion.line'].get_operations_recursion(self)
