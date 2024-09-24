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

    def _prepare_in_svl_vals(self, quantity, unit_cost):
        res = super(ProductProduct, self)._prepare_in_svl_vals(quantity, unit_cost)
        inventory_value = self.env.context.get('inventory_value', False)
        if self.env.context.get('is_quant', False) and inventory_value:
            company_id = self.env.context.get('force_company', self.env.company.id)
            company = self.env['res.company'].browse(company_id)
            value = company.currency_id.round(inventory_value * quantity)
            res.update(unit_cost=inventory_value, value=value, remaining_value=value)
        return res
