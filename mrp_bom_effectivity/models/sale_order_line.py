# -*- coding: utf-8 -*-
# © 2016 Scott Saunders - Asphalt Zipper, Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api
from openerp.tools import float_compare


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # override sale_mrp/sale_mrp
    @api.multi
    def _get_delivered_qty(self):
        self.ensure_one()
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # In the case of a kit, we need to check if all components are shipped. We use a all or
        # nothing policy. A product can have several BoMs, we don't know which one was used when the
        # delivery was created.
        bom_delivered = {}
        for bom in self.product_id.product_tmpl_id.bom_ids:
            if bom.type != 'phantom':
                continue
            ctx = dict(self.env.context or {})
            ctx.update({'bom_effectivity_date': getattr(self.order_id, 'effective_date', self.order_id.date_order)})
            bom_delivered[bom.id] = False
            product_uom_qty_bom = self.env['product.uom']._compute_qty_obj(self.product_uom, self.product_uom_qty, bom.product_uom)
            bom_exploded = self.env['mrp.bom'].with_context(ctx)._bom_explode(bom, self.product_id, product_uom_qty_bom)[0]
            for bom_line in bom_exploded:
                qty = 0.0
                for move in self.procurement_ids.mapped('move_ids'):
                    if move.state == 'done' and move.product_id.id == bom_line.get('product_id', False):
                        qty += self.env['product.uom']._compute_qty(move.product_uom.id, move.product_uom_qty, bom_line['product_uom'])
                if float_compare(qty, bom_line['product_qty'], precision_digits=precision) < 0:
                    bom_delivered[bom.id] = False
                    break
                else:
                    bom_delivered[bom.id] = True
        if bom_delivered and any(bom_delivered.values()):
            return self.product_uom_qty
        elif bom_delivered:
            return 0.0
        return super(SaleOrderLine, self)._get_delivered_qty()
