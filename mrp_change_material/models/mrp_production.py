# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.tools import float_round
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.multi
    def action_assign(self):
        for production in self:
            # confirm raw material stock moves added by the user
            move_to_assign = production.move_raw_ids.filtered(lambda x: x.state == 'draft')
            warehouse_id = production.location_src_id.get_warehouse().id
            for move in move_to_assign:
                loc = move.product_id.property_stock_production
                move.warehouse_id = warehouse_id
                move.location_dest_id = loc
                move.unit_factor = move.product_uom_qty / production.product_qty
            move_to_assign.action_confirm()
        return super(MrpProduction, self).action_assign()

    @api.multi
    def post_inventory(self):
        for order in self:

            # Check for Draft Moves
            # Any draft moves will be canceled, rather than posted, when posting inventory.  The action_assign() method
            # sets draft moves to confirmed.
            # The action_assign() method also creates stock.move.lots records for the new raw materials.  Without these,
            # it seems that the consumed quantity is posted as zero.
            if order.move_raw_ids.filtered(lambda x: x.state == 'draft'):
                raise UserError(_('You have new raw materials. Check availability again.'))

            # When the user adds RM then updates qty to produce, the qty to consume must be updated.
            # This case is NOT handled by simply setting the unit_factor field on the stock moves.
            # The ChangeProductionQty wizard only updates stock moves having a bom_line_id, and our added raw
            # materials didn't come from the BOM, so they don't get updated.
            # We can handle this here for non-tracked raw materials.  It may not behave as expected when there isn't
            # enough material to reserve the increased quantity.
            # TODO: This really should be handled by customizing the change.production.qty wizard
            moves_added = order.move_raw_ids.filtered(
                lambda x: (x.has_tracking == 'none') and (x.state not in ('done', 'cancel')) and x.added_rm)
            for move in moves_added:
                if move.unit_factor:
                    rounding = move.product_uom.rounding
                    move.quantity_done = float_round(order.product_qty * move.unit_factor, precision_rounding=rounding)

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
