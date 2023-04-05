from odoo import models, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _run_valuation(self, quantity=None):
        self.ensure_one()
        res = super(StockMove, self)._run_valuation(quantity)
        if self.production_id and self.production_id.product_id != self.product_id:
            # Modify product value
            by_product_moves = self.production_id.move_finished_ids.filtered(
                lambda x: x.product_id == self.product_id and x.state != 'cancel').mapped('value')
            finished_mo_product = self.production_id.move_finished_ids.filtered(
                lambda x: x.product_id == self.production_id.product_id and x.state != 'cancel')
            if by_product_moves and finished_mo_product:
                finished_mo_product.value = finished_mo_product.value - sum(by_product_moves)
                finished_mo_product.remaining_value = finished_mo_product.remaining_value - sum(by_product_moves)
                # don't update the price_unit field
                # see comments in OCA stock_inventory_revaluation module
                # finished_mo_product.price_unit = (finished_mo_product.price_unit - sum(by_product_moves)) \
                #     / finished_mo_product.product_qty
        return res
