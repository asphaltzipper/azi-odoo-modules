from odoo import models, fields, api
from odoo.tools import float_utils


class StockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    product_cost = fields.Float('Cost')

    def _generate_moves(self):
        vals_list = []
        for line in self:
            if float_utils.float_compare(line.theoretical_qty, line.product_qty, precision_rounding=line.product_id.uom_id.rounding) == 0:
                continue
            diff = line.theoretical_qty - line.product_qty
            if diff < 0:  # found more than expected
                vals = line._get_move_values(abs(diff), line.product_id.property_stock_inventory.id, line.location_id.id, False)
                vals.update(price_unit=line.product_cost)
            else:
                vals = line._get_move_values(abs(diff), line.location_id.id, line.product_id.property_stock_inventory.id, True)
            vals_list.append(vals)
        return self.env['stock.move'].create(vals_list)
