from odoo import api, fields, models, _


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    remaining_qty = fields.Float(copy=False)

    def write(self, values):
        if 'remaining_qty' not in values:
            for ml in self:
                values['remaining_qty'] = values.get('qty_done', ml.qty_done)
        return super(StockMoveLine, self).write(values)

    @api.model
    def create(self, values):
        if 'remaining_qty' not in values:
            values['remaining_qty'] = values.get('qty_done', 0.0)
        return super(StockMoveLine, self).create(values)
