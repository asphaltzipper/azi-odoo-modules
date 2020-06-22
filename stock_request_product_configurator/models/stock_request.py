# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockRequest(models.Model):
    _inherit = 'stock.request'

    @api.multi
    def action_config_start(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.configurator.stock.request',
            'name': "Product Configurator",
            'view_mode': 'form',
            'target': 'new',
            'context': dict(
                self.env.context,
                default_stock_request_id=self.id,
                wizard_model='product.configurator.stock.request',
            ),
        }
