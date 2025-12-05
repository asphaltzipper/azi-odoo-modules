from odoo import models, fields


class StockLotDtcLog(models.Model):
    _name = 'stock.lot.dtc.log'
    _description = 'Serialized Unit DTC Logs'

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
    spn = fields.Char(
        string='SPN',
        help="Suspect Parameter Number",
    )
    fmi = fields.Char(
        string='FMI',
        help="Failure Mode Indicator",
    )
    addr = fields.Char(
        string='Address',
        help="Source Address",
    )
    ocr = fields.Char(
        string='Occurrences',
        help="Number of occurrences",
    )
    note = fields.Char(string="Note")
