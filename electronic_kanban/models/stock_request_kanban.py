from odoo import api, fields, models


class StockRequestKanban(models.Model):
    _inherit = "stock.request.kanban"

    verify_date = fields.Date(
        string="Verify Date",
        help="Date of the latest scan of the barcode on this kanban",
    )
