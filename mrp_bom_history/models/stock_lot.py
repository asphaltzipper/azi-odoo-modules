from odoo import models


class StockLot(models.Model):
    _inherit = 'stock.lot'

    def action_open_bom_history(self):
        self.ensure_one()
        production = self.env['mrp.production'].search([('lot_producing_id', '=', self.id)])
        if production:
            return (self.env['ir.actions.report'].search([('report_name', '=', 'mrp_bom_history.report_bom_history')],
                                                         limit=1).report_action([production.id]))
