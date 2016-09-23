# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, float_round


class Product(models.Model):
    _inherit = "product.product"

    @api.multi
    def _get_mrp_planned_quantity(self, to_date=None):
        """Get total net move quantity of planned orders for specified products"""

        # build domain for searching mrp.material_plan records
        domain = [('product_id', 'in', self.ids)]
        if to_date:
            domain += [('date_finish', '<', datetime.strftime(to_date, DEFAULT_SERVER_DATE_FORMAT))]
        domain_in = domain + [('move_type', '=', 'supply')]
        domain_out = [('move_type', '=', 'demand')]

        # get moves
        MrpPlan = self.env['mrp.material_plan']
        moves_in = dict((item['product_id'][0], item['product_qty']) for item in
                        MrpPlan.read_group(domain_in, ['product_id', 'product_qty'], ['product_id']))
        moves_out = dict((item['product_id'][0], item['product_qty']) for item in
                         MrpPlan.read_group(domain_out, ['product_id', 'product_qty'], ['product_id']))

        # return dict
        res = dict()
        for product in self.with_context(prefetch_fields=False):
            qty = moves_in.get(product.id, 0.0) - moves_out.get(product.id, 0.0)
            res[product.id] = float_round(qty, precision_rounding=product.uom_id.rounding)
        return res
