from odoo import models, fields


class StockLotPartner(models.Model):
    _name = 'stock.lot.partner'
    _description = 'Serialized Unit Ownership History'

    owner_date = fields.Date(
        string='Acquired date',
        required=True,
        default=fields.Date.today,
    )

    lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Serial',
        required=True,
    )

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required='True',
    )

    note = fields.Char(string="Note")
