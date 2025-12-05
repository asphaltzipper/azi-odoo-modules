from odoo import models, fields


class StockLotGpsLog(models.Model):
    _name = 'stock.lot.gps.log'
    _description = 'Serialized Unit GPS Logs'

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
    lat = fields.Char(string='Latitude')
    long = fields.Char(string='Longitude')
    note = fields.Char(string="Note")
