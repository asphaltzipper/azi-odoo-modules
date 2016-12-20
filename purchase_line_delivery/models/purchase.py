# -*- coding: utf-8 -*-
# See __openerp__.py file for full copyright and licensing details.

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    default_carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Shipping',
        required=True)

    @api.onchange('partner_id', 'company_id')
    def onchange_partner_id(self):
        super(PurchaseOrder, self).onchange_partner_id()
        if not self.partner_id:
            self.default_carrier_id = False
        else:
            self.default_carrier_id = self.partner_id.property_delivery_carrier_id


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Shipping',
        required=True)

    @api.onchange('product_id', 'order_id')
    def onchange_product_id(self):
        result = super(PurchaseOrderLine, self).onchange_product_id()
        if not self.product_id:
            return result
        self.carrier_id = self.order_id.default_carrier_id
        return result
