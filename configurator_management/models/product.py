from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    attribute_value_product_ids = fields.One2many(
        comodel_name='attribute.value.products.report',
        inverse_name='product_tmpl_id')

    @api.multi
    def copy(self, default=None):
        if not default:
            default = {}
        res = super(ProductTemplate, self).copy(default=default)

        # copy active boms
        if self.config_ok:
            old_boms = self.env['mrp.bom'].search([
                ('product_tmpl_id', '=', self.id),
                ('product_id', '=', False),
            ])
            for bom in old_boms:
                defaults = {
                    'product_tmpl_id': res.id,
                }
                bom.copy(default=defaults)

        return res
