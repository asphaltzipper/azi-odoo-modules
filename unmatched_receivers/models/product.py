# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    unmatched_receiver_count = fields.Integer(compute='_compute_unmatched_receiver_count',
                                              string='Unmatched Receivers')

    @api.multi
    def _compute_unmatched_receiver_count(self):
        domain = [
            ('state', 'in', ['purchase', 'done']),
            ('product_id', 'in', self.mapped('id')),
            ('show_product_received', '=', True)
        ]
        PurchaseOrderLines = self.env['purchase.order.line'].search(domain)
        for product in self:
            product.unmatched_receiver_count = len(PurchaseOrderLines.filtered(lambda r: r.product_id == product).mapped('order_id'))


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    unmatched_receiver_count = fields.Integer(compute='_compute_unmatched_receiver_count',
                                              string='Unmatched Receivers')

    @api.multi
    def _compute_unmatched_receiver_count(self):
        for template in self:
            template.unmatched_receiver_count = sum([p.unmatched_receiver_count for p in template.product_variant_ids])
