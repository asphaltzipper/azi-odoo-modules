from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductConfigSession(models.Model):
    _inherit = "product.config.session"

    def ext_create_get_bom(self, variant_id, values=None):
        variant = self.env['product.product'].browse(variant_id)
        product_tmpl = variant.product_tmpl_id
        bom = self.create_get_bom(variant, product_tmpl, values)
        return bom and bom.id
