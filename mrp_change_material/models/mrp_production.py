# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.tools import float_round
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.multi
    def post_inventory(self):
        for order in self:

            # When the user adds RM then updates qty to produce, the qty to consume must be updated.
            # This case is NOT handled by simply setting the unit_factor field on the stock moves.
            # The ChangeProductionQty wizard only updates stock moves having a bom_line_id, and our added raw
            # materials didn't come from the BOM, so they don't get updated.
            # We can handle this here for non-tracked raw materials.  It may not behave as expected when there isn't
            # enough material to reserve the increased quantity.
            # TODO: This really should be handled by customizing the change.production.qty wizard
            finished_move = order.move_finished_ids.filtered(lambda x: x.product_id == order.product_id)
            finished_move_lines = finished_move.move_line_ids
            lot_produced = finished_move_lines and finished_move_lines[0].lot_id
            moves_added = order.move_raw_ids.filtered(
                lambda x: (x.has_tracking == 'none') and (x.state not in ('done', 'cancel')) and x.added_rm)
            for move in moves_added:
                if move.unit_factor:
                    rounding = move.product_uom.rounding
                    move.quantity_done = float_round(order.product_qty * move.unit_factor, precision_rounding=rounding)
                if lot_produced:
                    # assign all added consumption to the first lot produced
                    move.move_line_ids.update({'lot_produced_id': lot_produced.id})

            # There may be a gap here:
            # If the user adds serial-tracked raw material, after clicking the Plan button, the move_lot for the work
            # order doesn't get created.
            # If the user is using our work order completion wizard it's not a problem because he will be prompted for
            # the serial number.  That's what we will assume for now.
            # TODO: handle materials added after planning work orders
            # # This code needs some thoughtful consideration.  It was mostly copied from elsewhere, and may not behave
            # # as expected.
            # lot_moves_added = self.move_raw_ids.filtered(
            #     lambda x: (x.state not in ('done', 'cancel')) and x.added_rm)
            # for move_lot in lot_moves_added.mapped('move_lot_ids'):
            #
            #     # Check if move_lot already exists
            #     if move_lot.quantity_done <= 0:  # rounding...
            #         move_lot.sudo().unlink()
            #         continue
            #     if not move_lot.lot_id:
            #         raise UserError(_('You should provide a lot for a component'))
            #     # Search other move_lot where it could be added:
            #     lots = self.move_lot_ids.filtered(
            #         lambda x: (x.lot_id.id == move_lot.lot_id.id) and (not x.lot_produced_id) and (not x.done_move))
            #     if lots:
            #         lots[0].quantity_done += move_lot.quantity_done
            #         lots[0].lot_produced_id = self.final_lot_id.id
            #         move_lot.sudo().unlink()
            #     else:
            #         move_lot.lot_produced_id = self.final_lot_id.id
            #         move_lot.done_wo = True

        return super(MrpProduction, self).post_inventory()
