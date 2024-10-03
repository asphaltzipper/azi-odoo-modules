from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    config_ok = fields.Boolean(
        related="product_id.config_ok",
        store=True,
        string="Configurable",
        readonly=True,
    )
    re_config = fields.Boolean(string='Re-Configure')

    @api.constrains('product_id', 'product_tmpl_id', 'bom_line_ids', 're_config')
    def _check_product_recursion(self):
        for bom in self:
            if not bom.re_config:
                if bom.product_id:
                    if bom.bom_line_ids.filtered(
                        lambda x: x.product_id == bom.product_id
                    ):
                        raise ValidationError(_(
                            'BoM line product %s should not be same as BoM product.',
                            bom.display_name
                        ))
                else:
                    if bom.bom_line_ids.filtered(
                        lambda x: x.product_id.product_tmpl_id == bom.product_tmpl_id
                    ):
                        raise ValidationError(_(
                            'BoM line product %s should not be same as BoM product.',
                            bom.display_name
                        ))

    @api.constrains('product_id', 'config_ok', 're_config')
    def _check_product_required(self):
        # require product variant, unless this is a configurator bom
        for bom in self:
            if not bom.product_id and not bom.config_ok:
                raise ValidationError('Product Variant is required')
            if bom.product_id and bom.config_ok and not bom.re_config:
                raise ValidationError(
                    "Specifying a Product Variant, on a BOM for a configurable "
                    "product template, is only allowed on Re-Configure BOMs"
                )
