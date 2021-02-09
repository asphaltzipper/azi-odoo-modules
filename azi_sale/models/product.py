from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    sales_order_count = fields.Integer(compute='_sales_order_count', string='Sales')

    @api.multi
    def _sales_order_count(self):
        sales_lines = self.env['sale.order.line'].search([('state', '!=', 'cancel'),
                                                          ('product_id', 'in', self.mapped('id'))])
        for product in self:
            product.sales_order_count = len(sales_lines.filtered(lambda r: r.product_id == product).mapped('order_id'))


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    sales_order_count = fields.Integer(compute='_sales_order_count', string='Sales')

    @api.multi
    def _sales_order_count(self):
        for template in self:
            template.sales_order_count = sum([p.sales_order_count for p in template.product_variant_ids])
