from odoo import api, fields, models
from odoo.tools.float_utils import float_round


class ProductTemplate(models.Model):
    _inherit = "product.template"

    mrp_product_open_qty = fields.Float(
        string='Manufacturing',
        compute='_compute_mrp_product_open_qty',
    )

    @api.one
    def _compute_mrp_product_open_qty(self):
        self.mrp_product_open_qty = float_round(
            sum(self.mapped('product_variant_ids').mapped('mrp_product_open_qty')),
            precision_rounding=self.uom_id.rounding)

    @api.multi
    def action_view_actual_mos(self):
        action = self.env.ref('mrp.mrp_production_action').read()[0]
        action['domain'] = [('product_id', 'in', self.product_variant_ids.ids)]
        action['context'] = {'search_default_todo': 1}
        return action


class ProductProduct(models.Model):
    _inherit = "product.product"

    mrp_product_open_qty = fields.Float(
        string='Manufacturing',
        compute='_compute_mrp_product_open_qty',
    )

    def _compute_mrp_product_open_qty(self):
        domain = [
            ('state', 'not in', ['done', 'cancel']),
            ('product_id', 'in', self.ids)
        ]
        read_group_res = self.env['mrp.production'].read_group(
            domain, ['product_id', 'product_uom_qty'], ['product_id'])
        mapped_data = dict(
            [(data['product_id'][0], data['product_uom_qty']) for data in read_group_res])
        for product in self:
            product.mrp_product_open_qty = float_round(
                mapped_data.get(product.id, 0),
                precision_rounding=product.uom_id.rounding)

    @api.multi
    def action_view_actual_mos(self):
        action = self.env.ref('mrp.mrp_production_action').read()[0]
        action['domain'] = [('product_id', 'in', self.ids)]
        action['context'] = {'search_default_todo': 1}
        return action
