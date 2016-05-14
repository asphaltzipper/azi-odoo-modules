# -*- coding: utf-8 -*-
# © 2016 Matt Taylor - Asphalt Zipper
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, models, fields
from openerp.exceptions import ValidationError


class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    product_uom = fields.Many2one('product.uom', string='Purchase Unit of Measure', required=True, default=lambda self: self.product_tmpl_id.uom_po_id.id)
    uom_ref_id = fields.Many2one('product.uom', string='Product Stocking UOM', related='product_tmpl_id.uom_id', readonly=True)

    # enforce purchase uom category consistency against uom_ref_id
    @api.one
    @api.constrains('uom_ref_id', 'product_uom')
    def _check_uom(self):
        if self.uom_ref_id.category_id.id != self.product_uom.category_id.id:
            raise ValidationError("Error: The purchase Unit of Measure must be in the same category as the product's default stocking UOM.")
