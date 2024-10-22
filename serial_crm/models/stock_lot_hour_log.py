from odoo import models, fields


class StockLotHourLog(models.Model):
    _name = 'stock.lot.hour.log'
    _description = 'Serialized Unit Hour Logs'

    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.today(),
    )

    lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Serial',
        required=True,
    )

    hours = fields.Float(string='Hours')

    note = fields.Char(string="Note")
