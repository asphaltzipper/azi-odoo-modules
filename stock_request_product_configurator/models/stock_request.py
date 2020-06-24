# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockRequest(models.Model):
    _inherit = 'stock.request'

    product_id = fields.Many2one('product.product', 'Product', states={'draft': [('readonly', False)]}, required=False,
                                 readonly=True)
    product_uom_id = fields.Many2one('uom.uom', 'Product Unit of Measure', states={'draft': [('readonly', False)]},
                                     required=False, readonly=True)
    product_uom_qty = fields.Float(states={'draft': [('readonly', False)]}, readonly=True, default=1.0)

    @api.constrains('product_qty', 'product_id')
    def _check_qty(self):
        for rec in self:
            if rec.product_id and rec.product_qty <= 0:
                raise ValueError(_('Stock Request product quantity has to be strictly positive.'))

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = {'domain': {}}
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id
            res['domain']['product_uom_id'] = [
                ('category_id', '=', self.product_id.uom_id.category_id.id)]
            return res
        else:
            self.product_uom_id = False
        res['domain']['product_uom_id'] = []
        return res

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

    @api.multi
    def action_submit(self):
        if not self.product_id:
            raise ValidationError(_('Please set product before submitting request'))
        return super(StockRequest, self).action_submit()
