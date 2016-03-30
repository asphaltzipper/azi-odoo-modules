# -*- coding: utf-8 -*-
# © 2016 Scott Saunders - Asphalt Zipper, Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, SUPERUSER_ID
from openerp.exceptions import UserError
from openerp.tools.translate import _

class StockMove(models.Model):
    _inherit = 'stock.move'

    # override mrp/stock
    def _action_explode(self, cr, uid, move, context=None):
        """ Explodes pickings.
        @param move: Stock moves
        @return: True
        """
        if context is None:
            context = {}
        bom_obj = self.pool.get('mrp.bom')
        move_obj = self.pool.get('stock.move')
        prod_obj = self.pool.get("product.product")
        proc_obj = self.pool.get("procurement.order")
        uom_obj = self.pool.get("product.uom")
        to_explode_again_ids = []
        property_ids = context.get('property_ids') or []
        bis = bom_obj._bom_find(cr, SUPERUSER_ID, product_id=move.product_id.id, properties=property_ids, context={'bom_effectivity_date': move.date})
        bom_point = bom_obj.browse(cr, SUPERUSER_ID, bis, context=context)
        if bis and bom_point.type == 'phantom':
            ctx = context.copy()
            ctx['bom_effectivity_date'] = move.date
            processed_ids = []
            factor = uom_obj._compute_qty(cr, SUPERUSER_ID, move.product_uom.id, move.product_uom_qty, bom_point.product_uom.id) / bom_point.product_qty
            res = bom_obj._bom_explode(cr, SUPERUSER_ID, bom_point, move.product_id, factor, property_ids, context=ctx)

            for line in res[0]:
                product = prod_obj.browse(cr, uid, line['product_id'], context=context)
                if product.type in ['product', 'consu']:
                    valdef = {
                        'picking_id': move.picking_id.id if move.picking_id else False,
                        'product_id': line['product_id'],
                        'product_uom': line['product_uom'],
                        'product_uom_qty': line['product_qty'],
                        'state': 'draft',  #will be confirmed below
                        'name': line['name'],
                        'procurement_id': move.procurement_id.id,
                        'split_from': move.id, #Needed in order to keep sale connection, but will be removed by unlink
                        'price_unit': product.standard_price,
                    }
                    mid = move_obj.copy(cr, uid, move.id, default=valdef, context=context)
                    to_explode_again_ids.append(mid)
                else:
                    if product._need_procurement():
                        valdef = {
                            'name': move.rule_id and move.rule_id.name or "/",
                            'origin': move.origin,
                            'company_id': move.company_id and move.company_id.id or False,
                            'date_planned': move.date,
                            'product_id': line['product_id'],
                            'product_qty': line['product_qty'],
                            'product_uom': line['product_uom'],
                            'group_id': move.group_id.id,
                            'priority': move.priority,
                            'partner_dest_id': move.partner_id.id,
                            }
                        if move.procurement_id:
                            proc = proc_obj.copy(cr, uid, move.procurement_id.id, default=valdef, context=context)
                        else:
                            proc = proc_obj.create(cr, uid, valdef, context=context)
                        proc_obj.run(cr, uid, [proc], context=context) #could be omitted

            #check if new moves needs to be exploded
            if to_explode_again_ids:
                for new_move in self.browse(cr, uid, to_explode_again_ids, context=context):
                    processed_ids.extend(self._action_explode(cr, uid, new_move, context=context))

            if not move.split_from and move.procurement_id:
                # Check if procurements have been made to wait for
                moves = move.procurement_id.move_ids
                if len(moves) == 1:
                    proc_obj.write(cr, uid, [move.procurement_id.id], {'state': 'done'}, context=context)

            if processed_ids and move.state == 'assigned':
                # Set the state of resulting moves according to 'assigned' as the original move is assigned
                move_obj.write(cr, uid, list(set(processed_ids) - set([move.id])), {'state': 'assigned'}, context=context)

            #delete the move with original product which is not relevant anymore
            move_obj.unlink(cr, SUPERUSER_ID, [move.id], context=context)
            #return list of newly created move
            return processed_ids

        return [move.id]

    # override mrp/wizard/change_production_qty
    def change_prod_qty(self, cr, uid, ids, context=None):
        """
        Changes the Quantity of Product.
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: List of IDs selected
        @param context: A standard dictionary
        @return:
        """
        record_id = context and context.get('active_id',False)
        assert record_id, _('Active Id not found')
        prod_obj = self.pool.get('mrp.production')
        bom_obj = self.pool.get('mrp.bom')
        move_obj = self.pool.get('stock.move')
        uom_obj = self.pool.get('product.uom')
        for wiz_qty in self.browse(cr, uid, ids, context=context):
            prod = prod_obj.browse(cr, uid, record_id, context=context)
            prod_obj.write(cr, uid, [prod.id], {'product_qty': wiz_qty.product_qty})
            prod_obj.action_compute(cr, uid, [prod.id])

            for move in prod.move_lines:
                ctx = context and context.copy() or {}
                ctx['bom_effectivity_date'] = prod.date_planned
                bom_point = prod.bom_id
                bom_id = prod.bom_id.id
                if not bom_point:
                    bom_id = bom_obj._bom_find(cr, uid, product_id=prod.product_id.id, context=ctx)
                    if not bom_id:
                        raise UserError(_("Cannot find bill of material for this product."))
                    prod_obj.write(cr, uid, [prod.id], {'bom_id': bom_id})
                    bom_point = bom_obj.browse(cr, uid, [bom_id])[0]

                if not bom_id:
                    raise UserError(_("Cannot find bill of material for this product."))

                factor = uom_obj._compute_qty(cr, uid, prod.product_uom.id, prod.product_qty, bom_point.product_uom.id)
                product_details, workcenter_details = \
                    bom_obj._bom_explode(cr, uid, bom_point, prod.product_id, factor / bom_point.product_qty, [], context=ctx)
                for r in product_details:
                    if r['product_id'] == move.product_id.id:
                        move_obj.write(cr, uid, [move.id], {'product_uom_qty': r['product_qty']})
            if prod.move_prod_id:
                move_obj.write(cr, uid, [prod.move_prod_id.id], {'product_uom_qty' :  wiz_qty.product_qty})
            self._update_product_to_produce(cr, uid, prod, wiz_qty.product_qty, context=context)
        return {}
