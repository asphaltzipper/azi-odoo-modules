from odoo import models, fields, api, tools


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _prepare_in_svl_vals(self, quantity, unit_cost):
        res = super(ProductProduct, self)._prepare_in_svl_vals(quantity, unit_cost)
        inventory_value = self.env.context.get('inventory_value', False)
        if self.env.context.get('is_quant', False):
            company_id = self.env.context.get('force_company', self.env.company.id)
            company = self.env['res.company'].browse(company_id)
            value = company.currency_id.round(inventory_value * quantity)
            res.update(unit_cost=inventory_value, value=value, remaining_value=value)
        return res
