from odoo import api, fields, models


class ProductConfiguratorStockRequest(models.TransientModel):
    _name = 'product.configurator.stock.request'
    _inherit = 'product.configurator'

    stock_request_id = fields.Many2one('stock.request')

    def action_config_done(self):
        """Parse values and execute final code before closing the wizard"""
        res = super(ProductConfiguratorStockRequest, self).action_config_done()
        if res.get('res_model') == self._name:
            return res
        product = self.env['product.product'].browse(res['res_id'])
        self.stock_request_id.write({'product_id': product.id, 'product_uom_id': product.uom_id.id})
