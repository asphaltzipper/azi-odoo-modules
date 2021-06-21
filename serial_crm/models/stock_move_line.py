from odoo import models, fields, api, _


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    price_unit = fields.Float(
        related='move_id.price_unit',
    )
