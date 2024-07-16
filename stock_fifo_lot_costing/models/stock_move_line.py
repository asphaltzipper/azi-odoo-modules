from odoo import api, fields, models, _


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    remaining_qty = fields.Float(copy=False)

    def write(self, values):
        if 'qty_done' in values and 'remaining_qty' not in values:
            for ml in self:
                values['remaining_qty'] = values.get('qty_done')
        return super(StockMoveLine, self).write(values)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'remaining_qty' not in vals:
                vals['remaining_qty'] = vals.get('qty_done', 0.0)
        return super(StockMoveLine, self).create(vals_list)
