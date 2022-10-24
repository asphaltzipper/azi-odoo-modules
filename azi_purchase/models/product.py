from odoo import models, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def write(self, vals):
        if 'seller_ids' in vals:
            for seller_ids in vals['seller_ids']:
                if seller_ids[0] == 1 and 'price' in seller_ids[2]:
                    if 'name' not in seller_ids[2]:
                        supplier_info = self.env['product.supplierinfo'].browse(seller_ids[1])
                        supplier_name = supplier_info.name.display_name
                        price_from = supplier_info.price
                        message = "Purchase price changed from %s to %s for vendor %s" % (price_from,
                                                                                          seller_ids[2]['price'],
                                                                                          supplier_name)
                        self.message_post(body=message)
        return super(ProductProduct, self).write(vals)
