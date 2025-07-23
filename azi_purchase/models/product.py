from odoo import api, models, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    purchase_count = fields.Integer(compute='_purchase_count', string='# Purchases')

    def _purchase_count(self):
        """Include draft purchases in the count"""
        domain = [
            ('state', 'in', ['draft', 'purchase', 'done']),
            ('product_id', 'in', self.mapped('id')),
        ]
        PurchaseOrderLines = self.env['purchase.order.line'].search(domain)
        for product in self:
            product.purchase_count = len(
                PurchaseOrderLines.filtered(lambda r: r.product_id == product).mapped('order_id'))

    def write(self, vals):
        if 'seller_ids' in vals:
            for seller_ids in vals['seller_ids']:
                if seller_ids[0] == 1 and 'price' in seller_ids[2]:
                    if 'partner_id' not in seller_ids[2]:
                        supplier_info = self.env['product.supplierinfo'].browse(seller_ids[1])
                        supplier_name = supplier_info.partner_id.display_name
                        price_from = supplier_info.price
                        message = "Purchase price changed from %s to %s for vendor %s" % (
                            price_from, seller_ids[2]['price'], supplier_name)
                        self.message_post(body=message)
        return super(ProductProduct, self).write(vals)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    purchase_count = fields.Integer(compute='_purchase_count', string='# Purchases')

    def _purchase_count(self):
        for template in self:
            template.purchase_count = sum([p.purchase_count for p in template.product_variant_ids])
        return True
