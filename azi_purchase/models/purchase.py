# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import timedelta
from odoo import api, fields, models
from odoo.tools.float_utils import float_round


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    send_date = fields.Datetime(
        string='Date Sent'
    )

    @api.multi
    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        for line in self.mapped('order_line'):
            seller = line.product_id.seller_ids.filtered(lambda s: s.name == line.order_id.partner_id)
            if seller:
                seller = seller.sorted(key=lambda x: x.sequence)[0]
                if seller.price != line.price_unit:
                    message = "Purchase price changed from %s to %s for vendor %s" % (seller.price, line.price_unit,
                                                                                      seller.name.display_name)
                    seller.price = line.price_unit
                    line.product_id.message_post(body=message)
        return res


class ProductProduct(models.Model):
    _inherit = 'product.product'

    purchase_count = fields.Integer(compute='_purchase_count', string='# Purchases')

    @api.multi
    def _purchase_count(self):
        """Include draft purchases in the count"""
        domain = [
            ('state', 'in', ['draft', 'purchase', 'done']),
            ('product_id', 'in', self.mapped('id')),
        ]
        PurchaseOrderLines = self.env['purchase.order.line'].search(domain)
        for product in self:
            product.purchase_count = len(PurchaseOrderLines.filtered(lambda r: r.product_id == product).mapped('order_id'))

    @api.multi
    def _compute_purchased_product_qty(self):
        date_from = fields.Datetime.to_string(fields.datetime.now() - timedelta(days=365))
        domain = [
            ('state', 'in', ['draft', 'purchase', 'done']),
            ('product_id', 'in', self.mapped('id')),
            ('date_order', '>', date_from)
        ]
        PurchaseOrderLines = self.env['purchase.order.line'].search(domain)
        order_lines = self.env['purchase.order.line'].read_group(domain, ['product_id', 'product_uom_qty'],
                                                                 ['product_id'])
        purchased_data = dict([(data['product_id'][0], data['product_uom_qty']) for data in order_lines])
        for product in self:
            product.purchased_product_qty = float_round(purchased_data.get(product.id, 0),
                                                        precision_rounding=product.uom_id.rounding)

    @api.multi
    def action_view_po(self):
        action = self.env.ref('purchase.action_purchase_order_report_all').read()[0]
        action['domain'] = ['&', ('state', 'in', ['draft', 'purchase', 'done']), ('product_id', 'in', self.ids)]
        action['context'] = {
            'search_default_last_year_purchase': 1,
            'search_default_status': 1, 'search_default_order_month': 1,
            'graph_measure': 'unit_quantity'
        }
        return action


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    purchase_count = fields.Integer(compute='_purchase_count', string='# Purchases')

    @api.multi
    def _purchase_count(self):
        for template in self:
            template.purchase_count = sum([p.purchase_count for p in template.product_variant_ids])
        return True

    @api.multi
    def action_view_po(self):
        action = self.env.ref('purchase.action_purchase_order_report_all').read()[0]
        action['domain'] = ['&', ('state', 'in', ['draft', 'purchase', 'done']), ('product_tmpl_id', 'in', self.ids)]
        action['context'] = {
            'search_default_last_year_purchase': 1,
            'search_default_status': 1, 'search_default_order_month': 1,
            'graph_measure': 'unit_quantity'
        }
        return action


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail(self, auto_commit=False):
        if self._context.get('default_model') == 'purchase.order' and self._context.get('default_res_id'):
            if not self.filtered('subtype_id.internal'):
                order = self.env['purchase.order'].browse([self._context['default_res_id']])
                order.send_date = fields.datetime.now()
        return super(MailComposeMessage, self.with_context(mail_post_autofollow=True)).send_mail(auto_commit=auto_commit)
