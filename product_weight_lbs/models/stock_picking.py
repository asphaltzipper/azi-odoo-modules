# -*- coding: utf-8 -*-
# (c) 2017 Scott Saunders
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models

import odoo.addons.decimal_precision as dp


class StockPicking(models.Model):
    _inherit = "stock.picking"

    weight_in_lbs = fields.Float(
        string='Weight in lbs',
        digits=dp.get_precision('Stock Weight'),
        compute='_compute_weight_in_lbs',
        store=True
    )
    shipping_weight_in_lbs = fields.Float(
        string='Shipping Weight in lbs',
        digits=dp.get_precision('Stock Weight'),
        compute='_compute_shipping_weight_in_lbs'
    )

    @api.depends('weight')
    def _compute_weight_in_lbs(self):
        weight_uom_id = self.env.ref('product.product_uom_kgm')
        weight_in_lbs_uom_id = self.env.ref('product.product_uom_lb')
        for p in self:
            p.weight_in_lbs = weight_uom_id._compute_quantity(p.weight, weight_in_lbs_uom_id)

    @api.depends('shipping_weight')
    def _compute_shipping_weight_in_lbs(self):
        weight_uom_id = self.env.ref('product.product_uom_kgm')
        weight_in_lbs_uom_id = self.env.ref('product.product_uom_lb')
        for p in self:
            p.shipping_weight_in_lbs = weight_uom_id._compute_quantity(p.shipping_weight, weight_in_lbs_uom_id)
