from odoo import models, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def _run_fifo(self, quantity, company):
        if self.tracking == 'none':
            return super(ProductProduct, self)._run_fifo(quantity, company)
        self.ensure_one()
        # extra
        move = self.env.context.get('move', False)
        if move:
            rounding = move.product_uom.rounding
            valued_move_lines = move.move_line_ids.filtered(
                lambda ml: ml.location_id._should_be_valued() and not ml.location_dest_id._should_be_valued() and not ml.owner_id)
            candidates = self.env['stock.valuation.layer'].sudo().search([
                ('product_id', '=', self.id),
                ('remaining_qty', '>', 0),
                ('company_id', '=', company.id),
            ])
            # extra lots
            lots = valued_move_lines.mapped('lot_id')
            new_standard_price = 0
            tmp_value = 0  # to accumulate the value taken on the candidates
            qty_to_take_on_lots = {x: 0.0 for x in lots}

            for valued_move_line in valued_move_lines:
                lot = valued_move_line.lot_id
                qty_to_take_on_candidates = valued_move_line.product_uom_id._compute_quantity(
                    valued_move_line.qty_done, move.product_id.uom_id)
                qty_to_take_on_lots[lot] += qty_to_take_on_candidates
                for candidate in candidates:
                    if float_compare(candidate.remaining_qty,
                                     sum(candidate.stock_move_id.move_line_ids.mapped('remaining_qty')),
                                     precision_rounding=rounding) != 0:
                        raise UserError(_("Line remaining quantity does not match "
                                          "move remaining quantity for move %s" %
                                          candidate.stock_move_id.name))
                    for candidate_line in candidate.stock_move_id.move_line_ids.filtered(
                            lambda x: x.lot_id == lot and x.remaining_qty > 0.0):
                        qty_taken_on_candidate = min(qty_to_take_on_candidates, candidate_line.remaining_qty)
                        candidate_unit_cost = candidate.remaining_value / candidate.remaining_qty
                        new_standard_price = candidate_unit_cost
                        qty_to_take_on_lots[lot] -= qty_taken_on_candidate
                        value_taken_on_candidate = qty_taken_on_candidate * candidate_unit_cost
                        value_taken_on_candidate = candidate.currency_id.round(value_taken_on_candidate)
                        new_remaining_value = candidate.remaining_value - value_taken_on_candidate
                        candidate_line.write({
                            'remaining_qty': candidate_line.remaining_qty - qty_taken_on_candidate,
                        })
                        candidate.write({
                            'remaining_qty': candidate.remaining_qty - qty_taken_on_candidate,
                            'remaining_value': new_remaining_value,
                        })
                        # tmp_qty += qty_taken_on_candidate
                        tmp_value += value_taken_on_candidate

            unavailable_lots = self.env['stock.lot']
            for lot, qty in qty_to_take_on_lots.items():
                if qty > 0.0:
                    unavailable_lots |= lot
            if unavailable_lots:
                raise UserError(_("We can't process the move because the following "
                                  "lots/serials are not available: %s" %
                                  ", ".join(unavailable_lots.mapped('name'))))

            if new_standard_price and move.product_id.cost_method == 'fifo':
                self.sudo().with_company(company.id).with_context(disable_auto_svl=True).standard_price = new_standard_price
            vals = {
                'value': -tmp_value,
                'unit_cost': tmp_value / quantity,
            }
            return vals
