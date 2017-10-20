# -*- coding: utf-8 -*-

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    has_tracking = fields.Selection(store=True)


class StockMoveLots(models.Model):
    _inherit = 'stock.move.lots'

    lot_id = fields.Many2one(domain="[('product_id', '=', product_id), ('state', '=', 'inventory']")
    lot_produced_id = fields.Many2one(domain="[('product_id', '=', product_id), ('state', '=', 'assigned']")
