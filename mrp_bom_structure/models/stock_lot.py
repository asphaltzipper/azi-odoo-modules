from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockLot(models.Model):
    _inherit = 'stock.lot'

    def action_report_curr_bom(self):
        self.ensure_one()
        boms_by_product = self.env["mrp.bom"]._bom_find(self.product_id)
        bom = boms_by_product.get(self.product_id, self.env["mrp.bom"])
        report = self.env['ir.actions.report']._get_report_from_name(
            'mrp_bom_structure.bom_structure_down')
        action = report.report_action(bom.ids, config=False)
        if bom:
            return action
        else:
            raise UserError(_("No BOM found for this product"))
