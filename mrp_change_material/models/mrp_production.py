# -*- coding: utf-8 -*-

from odoo import api, models
from odoo.tools import float_round
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.multi
    def action_assign(self):
        for production in self:
            move_to_assign = production.move_raw_ids.filtered(lambda x: x.state == 'draft')
            warehouse_id = self.location_src_id.get_warehouse().id
            for move in move_to_assign:
                loc = move.product_id.property_stock_production
                move.warehouse_id = warehouse_id
                move.location_dest_id = loc
                move.unit_factor = move.product_uom_qty / self.product_qty
            move_to_assign.action_confirm()
        return super(MrpProduction, self).action_assign()

    @api.multi
    def post_inventory(self):
        for order in self:

            # Check for Draft Moves
            # TODO: unhandled case: user adds RM then updates qty to produce... qty to consume isn't updated
            if order.move_raw_ids.filtered(lambda x: x.state == 'draft'):
                raise UserError(_('You have new consumed materials. Check availability again.'))

            # Update quantities done on each raw material line
            moves_added = self.move_raw_ids.filtered(
                lambda x: (x.has_tracking == 'none') and (x.state not in ('done', 'cancel')) and x.added_rm)
            for move in moves_added:
                if move.unit_factor:
                    rounding = move.product_uom.rounding
                    move.quantity_done += float_round(self.product_qty * move.unit_factor,
                                                      precision_rounding=rounding)

            # Transfer quantities from temporary to final move lots or make them final
            lot_moves_added = self.move_raw_ids.filtered(
                lambda x: (x.state not in ('done', 'cancel')) and x.added_rm)
            for move_lot in lot_moves_added.mapped('move_lot_ids'):

                # Check if move_lot already exists
                if move_lot.quantity_done <= 0:  # rounding...
                    move_lot.sudo().unlink()
                    continue
                if not move_lot.lot_id:
                    raise UserError(_('You should provide a lot for a component'))
                # Search other move_lot where it could be added:
                # lots = self.move_lot_ids.filtered(
                #     lambda x: (x.lot_id.id == move_lot.lot_id.id) and (not x.lot_produced_id) and (not x.done_move))
                # if lots:
                #     lots[0].quantity_done += move_lot.quantity_done
                #     lots[0].lot_produced_id = self.final_lot_id.id
                #     move_lot.sudo().unlink()
                # else:
                #     move_lot.lot_produced_id = self.final_lot_id.id
                #     move_lot.done_wo = True

        return super(MrpProduction, self).post_inventory()
