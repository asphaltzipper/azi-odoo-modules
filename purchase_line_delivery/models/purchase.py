# -*- coding: utf-8 -*-
# See __openerp__.py file for full copyright and licensing details.

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def _get_default_carrier(self):
        if self.partner_id.property_delivery_carrier_id:
            return self.partner_id.property_delivery_carrier_id.id
        if self.env['ir.config_parameter'].sudo().get_param('purchase_line_delivery.po_carrier_id'):
            return int(self.env['ir.config_parameter'].sudo().get_param('purchase_line_delivery.po_carrier_id'))
        return self.env['delivery.carrier'].search([], limit=1, order='sequence').id

    default_carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Shipping',
        required=True,
        default=_get_default_carrier)

    @api.onchange('partner_id', 'company_id')
    def onchange_partner_id(self):
        super(PurchaseOrder, self).onchange_partner_id()
        if not self.partner_id:
            self.default_carrier_id = False
        else:
            self.default_carrier_id = self._get_default_carrier()

    @api.multi
    def action_set_shipping(self):
        for purchase_order in self:
            purchase_order.order_line.update({'carrier_id': purchase_order.default_carrier_id})


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.model
    def _get_default_carrier(self):
        if self._context.get('default_carrier_id'):
            return self.env.context['default_carrier_id']
        if self.order_id.partner_id:
            return self.order_id.partner_id.property_delivery_carrier_id.id
        if self.env['ir.config_parameter'].sudo().get_param('purchase_line_delivery.po_carrier_id'):
            return int(self.env['ir.config_parameter'].sudo().get_param('purchase_line_delivery.po_carrier_id'))
        return self.env['delivery.carrier'].search([], limit=1, order='sequence').id

    carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Shipping',
        default=_get_default_carrier)

    @api.onchange('product_id', 'order_id')
    def onchange_product_id(self):
        result = super(PurchaseOrderLine, self).onchange_product_id()
        if self.product_id:
            self.carrier_id = self.order_id.default_carrier_id
        return result

