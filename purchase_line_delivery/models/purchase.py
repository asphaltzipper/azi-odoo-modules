# -*- coding: utf-8 -*-
# See __openerp__.py file for full copyright and licensing details.

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def _get_default_carrier(self):
        if self.partner_id and self.partner_id.property_delivery_carrier_id:
            return self.partner_id.property_delivery_carrier_id.id
        elif self.env['ir.values'].get_default('purchase.config.settings', 'po_carrier_id'):
            return self.env['ir.values'].get_default('purchase.config.settings', 'po_carrier_id')
        else:
            return self.env['delivery.carrier'].search([], limit=1, order='sequence').id

    @api.onchange('partner_id', 'company_id')
    def onchange_partner_id(self):
        super(PurchaseOrder, self).onchange_partner_id()
        if not self.partner_id:
            self.default_carrier_id = False
        else:
            self.default_carrier_id = self._get_default_carrier()

    default_carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Shipping',
        required=True,
        default=_get_default_carrier)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.model
    def _get_default_carrier(self):
        if self.order_id.partner_id:
            return self.order_id.partner_id.property_delivery_carrier_id.id
        else:
            return self.env['res.partner'].browse(1).property_delivery_carrier_id.id

    carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Shipping',
        required=True,
        default=_get_default_carrier)

    @api.onchange('product_id', 'order_id')
    def onchange_product_id(self):
        result = super(PurchaseOrderLine, self).onchange_product_id()
        if self.product_id:
            self.carrier_id = self.order_id.default_carrier_id
        return result

