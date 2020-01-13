# -*- coding: utf-8 -*-
# (c) 2017 Scott Saunders
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models

import odoo.addons.decimal_precision as dp


class ProductTemplate(models.Model):
    _inherit = "product.template"

    weight_in_lbs = fields.Float(
        string='Weight in lbs',
        digits=dp.get_precision('Stock Weight'),
        compute='_compute_weight_in_lbs',
        inverse='_set_weight_in_lbs',
        store=True,
        help="The weight of the contents in lbs, not including any packaging, etc."
    )

    @api.model
    def _init_weight_in_lbs(self):
        """ Initialize new field on module install """
        cr = self._cr
        cr.execute("""update product_template
                   set weight_in_lbs = round(weight/0.45359237, 2)
        """)

    @api.depends('weight_in_lbs')
    def _compute_weight(self):
        weight_in_lbs_uom_id = self.env.ref('uom.product_uom_lb')
        weight_uom_id = self.env.ref('uom.product_uom_kgm')
        for p in self:
            p.weight = weight_in_lbs_uom_id._compute_quantity(p.weight_in_lbs, weight_uom_id)

    @api.model
    def create(self, vals):
        """ Trigger an update of new field for the first variant """
        template = super(ProductTemplate, self).create(vals)
        # This is needed to set given value to first variant after creation
        related_vals = {}
        if vals.get('weight_in_lbs'):
            related_vals['weight_in_lbs'] = vals['weight_in_lbs']
        template.write(related_vals)
        return template

    @api.depends('product_variant_ids', 'product_variant_ids.weight_in_lbs')
    def _compute_weight_in_lbs(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.weight_in_lbs = template.product_variant_ids.weight_in_lbs
        for template in (self - unique_variants):
            template.weight_in_lbs = 0.0

    def _set_weight_in_lbs(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.weight_in_lbs = self.weight_in_lbs
