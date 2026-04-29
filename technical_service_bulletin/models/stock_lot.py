from odoo import models, fields


class StockLot(models.Model):
    _inherit = 'stock.lot'

    tsb_bulletin_ids = fields.One2many(
        comodel_name='tsb.serial',
        inverse_name='lot_id',
        string="TSBs",
    )
