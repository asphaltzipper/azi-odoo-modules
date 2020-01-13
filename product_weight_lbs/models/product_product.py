# -*- coding: utf-8 -*-
# (c) 2017 Scott Saunders
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class ProductProduct(models.Model):
    _inherit = "product.product"

    weight_in_lbs = fields.Float(
        string='Weight in lbs',
        digits=dp.get_precision('Stock Weight'),
        help="The weight of the contents in lbs, not including any packaging, etc."
    )
    weight = fields.Float(
        string='Weight (Default UoM)',
        compute='_compute_weight',
        store=True
    )

    @api.model
    def _init_weight_in_lbs(self):
        """ Initialize new field on module install """
        cr = self._cr
        cr.execute("""update product_product
                   set weight_in_lbs = round(weight/0.45359237, 2)
        """)

    @api.depends('weight_in_lbs')
    def _compute_weight(self):
        weight_in_lbs_uom_id = self.env.ref('uom.product_uom_lb')
        weight_uom_id = self.env.ref('uom.product_uom_kgm')
        for p in self:
            p.weight = weight_in_lbs_uom_id._compute_quantity(p.weight_in_lbs, weight_uom_id)
