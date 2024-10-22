from odoo import models, fields


class StockLotNote(models.Model):
    _name = 'stock.lot.note'
    _description = 'Serialized Unit Notes'
    _order = 'create_date desc'

    name = fields.Text(
        string='Note',
        required=True,
    )

    lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Serial',
        required=True,
    )
