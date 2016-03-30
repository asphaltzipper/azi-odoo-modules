# -*- coding: utf-8 -*-
# © 2016 Scott Saunders - Asphalt Zipper, Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models
from openerp.tools import float_compare


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # override purchase/purchase
    def _get_bom_delivered(self, line):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        bom_delivered = {}
        # There is no dependencies between purchase and mrp
        if 'mrp.bom' in self.env:
            # In the case of a kit, we need to check if all components are shipped. We use a all or
            # nothing policy. A product can have several BoMs, we don't know which one was used when the
            # delivery was created.
            for bom in line.product_id.product_tmpl_id.bom_ids:
                if bom.type != 'phantom':
                    continue
                bom_delivered[bom.id] = False
                bom_exploded = self.env['mrp.bom']._bom_explode(bom, line.product_id, line.product_qty)[0]
                for bom_line in bom_exploded:
                    qty = 0.0
                    for move in line.move_ids:
                        if move.state == 'done' and move.product_id.id == bom_line.get('product_id', False):
                            qty += self.env['product.uom']._compute_qty_obj(move.product_uom, move.product_uom_qty, self.product_uom)
                    if float_compare(qty, bom_line['product_qty'], precision_digits=precision) < 0:
                        bom_delivered[bom.id] = False
                        break
                    else:
                        bom_delivered[bom.id] = True
        return bom_delivered
