# -*- coding: utf-8 -*-
# © 2016 Matt Taylor - Asphalt Zipper
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def get_purchase_uom(self, supplier=False):
        self.ensure_one()
        # TODO: calculate and return a purchase UOM
        # if no supplier specified, or supplier not found, then return uom_po_id from product template
        # if a matching supplier is found, then return the purchase unit of measure from the supplierinfo record
        pass
