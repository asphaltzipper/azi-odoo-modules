from odoo import models, fields, api, tools


class ProductTemplate(models.Model):
    _inherit = "product.template"

    code128 = fields.Char(
        related='product_variant_ids.code128',
        readonly=True,
        store=True,
    )


class ProductProduct(models.Model):
    _inherit = "product.product"

    code128 = fields.Char(
        string="Code128 Encoded PN",
        compute="_compute_code128",
        store=True,
    )

    @api.depends('default_code')
    def _compute_code128(self):
        for prod in self:
            if not prod.default_code:
                prod.code128 = False
                continue
            prod.code128 = self.env['barcode.nomenclature'].get_code128_encoding(prod.default_code)
