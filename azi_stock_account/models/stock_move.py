from odoo import models, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _create_in_svl(self, forced_quantity=None):
        """Create a `stock.valuation.layer` from `self`.

        :param forced_quantity: under some circunstances, the quantity to value is different than
            the initial demand of the move (Default value = None)
        """
        svl_vals_list = self._get_in_svl_vals(forced_quantity)
        return self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

    def _get_in_svl_vals(self, forced_quantity):
        svl_vals_list = super(StockMove, self)._get_in_svl_vals(forced_quantity)
        active_model = self.env.context.get('active_model', False)
        for move in self:
            if active_model == 'mrp.production':
                production = self.env['mrp.production'].search([('name', '=', move.origin)])
                if production.bom_id.reconfigure:
                    byproduct_ids = production.move_byproduct_ids
                    if byproduct_ids:
                        if move.product_id.id not in byproduct_ids.mapped('product_id.id'):
                            byproduct_values = sum([byproduct.product_qty * byproduct.product_id.standard_price for byproduct in byproduct_ids])
                            consumed = abs(sum(self.env['stock.valuation.layer'].search(
                                [('reference', '=', move.origin), ('value', '<', 0)]).mapped('value')))
                            value_of_mo = consumed - byproduct_values
                            unit_cost = value_of_mo / move.product_qty
                            svl_vals_list = [
                                {**vals, 'remaining_value': value_of_mo, 'value': value_of_mo, 'unit_cost': unit_cost}
                                if vals['stock_move_id'] == move.id else vals
                                for vals in svl_vals_list
                            ]
                        else:
                            product_value = move.product_id.standard_price * move.product_qty
                            unit_cost = move.product_id.standard_price
                            svl_vals_list = [
                                {**vals, 'remaining_value': product_value, 'value': product_value, 'unit_cost': unit_cost}
                                if vals['stock_move_id'] == move.id else vals
                                for vals in svl_vals_list
                            ]
        return svl_vals_list

