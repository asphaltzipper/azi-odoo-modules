from odoo import models, fields


class StockLotGpsLog(models.Model):
    _name = 'stock.lot.gps.log'
    _description = 'Serialized Unit GPS Logs'
    _order = 'date desc'

    date = fields.Datetime(
        string='Date',
        required=True,
        default=fields.Datetime.now(),
    )
    lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Serial',
        required=True,
    )
    lat = fields.Char(string='Latitude')
    long = fields.Char(string='Longitude')
    note = fields.Char(string="Note")
