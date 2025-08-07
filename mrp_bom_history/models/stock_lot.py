from odoo import models


class StockLot(models.Model):
    _inherit = 'stock.lot'

    def action_open_bom_history(self):
        self.ensure_one()
        production = self.env['mrp.production'].search([('lot_producing_id', '=', self.id)])
        return {
            'type': 'ir.actions.act_window',
            'name': 'BOM History',
            'res_model': 'mrp.bom.history.line',
            'target': 'current',
            'view_mode': 'tree',
            'domain': [('production_id', '=', production.id), ('production_id', '!=', False)]
        }

