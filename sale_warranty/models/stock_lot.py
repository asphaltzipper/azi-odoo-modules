from odoo import models, fields


class StockLot(models.Model):
    _inherit = 'stock.lot'

    warranty_ids = fields.One2many(
        comodel_name='sale.warranty',
        inverse_name='lot_id',
        string="Warranty",
    )
