# -*- coding: utf-8 -*-

from odoo import models, fields


class StockLotPartner(models.Model):
    _name = 'stock.lot.partner'

    owner_date = fields.Date(
        string='Acquired date',
        required=True,
        default=fields.Date.today)

    lot_id = fields.Many2one(
        comodel_name='stock.production.lot',
        string='Serial')

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        domain=[('customer', '=', True)])
