from odoo import fields, models


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    post_date = fields.Date(
        related="account_move_id.date",
        string="Post Date",
        store=True,
    )
