from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    preserve_bom_on_import = fields.Boolean(
        related='product_variant_ids.preserve_bom_on_import',
        readonly=False)


class ProductProduct(models.Model):
    _inherit = "product.product"

    preserve_bom_on_import=fields.Boolean(
        string='Preserve BOM',
        default=False,
        required=True,
        help="Keep the existing BOM, and ignore imported BOMs for this product")
