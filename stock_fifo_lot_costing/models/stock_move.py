from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.model
    def _get_move_lot_avail_qty(self, lots):
        """get quantity available by lot for inbound moves of tracked products"""
        # the candidate move may have lines from multiple lots
        # we consume candidate lines in order by lot
        # we must calculate the quantity available for the lots of each move
        data = self.env['stock.move.line'].read_group(
            # domain=[('move_id', 'in', self.ids),
            #         ('lot_id', 'in', lots.ids)],
            domain=[('move_id', 'in', self.ids)],
            fields=['move_id', 'lot_id', 'qty_done'],
            groupby=['move_id', 'lot_id'],
            orderby='move_id, lot_id',
            lazy=False,
        )
        move_lines = {(x['move_id'][0], x['lot_id'][0]): x for x in data}
        # build data structure for move_lots_qty:
        #   {
        #      move_id: {
        #         'to_use_qty': product_qty-remaining_qty,
        #         'used_qty': 0,
        #         'lots': {
        #            lot_id: qty_avail
        #         }
        #      }
        #   }
        move_lots_qty = {}
        for x in self:
            move_lots_qty[x.id] = {
                'to_use_qty': x.product_qty - x.remaining_qty,
                'used_qty': 0.0,
                'lots': {}
            }
        for line in data:
            move_id = line['move_id'][0]
            lot_id = line['lot_id'][0]
            used_qty = move_lots_qty[move_id]['used_qty']
            to_use_qty = move_lots_qty[move_id]['to_use_qty']
            lot_use_qty = min(line['qty_done'], to_use_qty - used_qty)
            lot_avail_qty = line['qty_done'] - lot_use_qty
            move_lots_qty[move_id]['used_qty'] += lot_use_qty
            move_lots_qty[move_id]['lots'][lot_id] = lot_avail_qty

        return move_lots_qty

    @api.model
    def _run_fifo(self, move, quantity=None):
        """Get cost from the consumed lots.  If the product is not tracked, call the original _run_fifo method"""
        if move.product_id.tracking == 'none':
            return super(StockMove, self)._run_fifo(move, quantity)

        move.ensure_one()
        rounding = move.product_uom.rounding
        valued_move_lines = move.move_line_ids.filtered(lambda ml: ml.location_id._should_be_valued() and not ml.location_dest_id._should_be_valued() and not ml.owner_id)
        candidates = move.product_id._get_fifo_candidates_in_move_with_company(move.company_id.id)
        lots = valued_move_lines.mapped('lot_id')
        new_standard_price = 0
        tmp_qty = 0
        tmp_value = 0  # to accumulate the value taken on the candidates

        qty_to_take_on_lots = {x: 0.0 for x in lots}
        for valued_move_line in valued_move_lines:
            lot = valued_move_line.lot_id
            qty_to_take_on_candidates = valued_move_line.product_uom_id._compute_quantity(
                valued_move_line.qty_done, move.product_id.uom_id)
            qty_to_take_on_lots[lot] += qty_to_take_on_candidates

            for candidate in candidates:

                # ensure line remaining_qty sums to move remaining_qty
                if float_compare(
                        candidate.remaining_qty,
                        sum(candidate.move_line_ids.mapped('remaining_qty')),
                        precision_rounding=rounding) != 0:
                    raise UserError(_("Line remaining quantity does not match "
                                       "move remaining quantity for move %s" %
                                       candidate.name))

                for candidate_line in candidate.move_line_ids.filtered(
                        lambda x: x.lot_id == lot and x.remaining_qty > 0.0):
                    new_standard_price = candidate.price_unit
                    qty_taken_on_candidate = min(candidate_line.remaining_qty,
                                                 qty_to_take_on_candidates)
                    qty_to_take_on_lots[lot] -= qty_taken_on_candidate
                    candidate_price_unit = candidate.remaining_value / candidate.remaining_qty
                    value_taken_on_candidate = qty_taken_on_candidate * candidate_price_unit
                    candidate_line_vals = {
                        'remaining_qty': candidate_line.remaining_qty - qty_taken_on_candidate,
                    }
                    candidate_line.write(candidate_line_vals)
                    candidate_vals = {
                        'remaining_qty': candidate.remaining_qty - qty_taken_on_candidate,
                        'remaining_value': candidate.remaining_value - value_taken_on_candidate,
                    }
                    candidate.write(candidate_vals)
                    tmp_qty += qty_taken_on_candidate
                    tmp_value += value_taken_on_candidate

        unavailable_lots = self.env['stock.production.lot']
        for lot, qty in qty_to_take_on_lots.items():
            if qty > 0.0:
                unavailable_lots += lot
        if unavailable_lots:
            raise UserError(_("We can't process the move because the following "
                              "lots/serials are not available: %s" %
                              ", ".join(unavailable_lots.mapped('name'))))

        # Update the standard price with the price of the last used candidate, if any.
        if new_standard_price and move.product_id.cost_method == 'fifo':
            move.product_id.sudo().with_context(force_company=move.company_id.id) \
                .standard_price = new_standard_price

        if not move.value:
            price_unit = -tmp_value / (move.product_qty or quantity)
        else:
            price_unit = (-(tmp_value) + move.value) / (tmp_qty + move.product_qty)
        move.write({
            'value': -tmp_value if not quantity else move.value or -tmp_value,  # outgoing move are valued negatively
            'price_unit': price_unit,
        })

        return tmp_value
