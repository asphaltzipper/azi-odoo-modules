# -*- coding: utf-8 -*-

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    has_tracking = fields.Selection(
        related='product_id.tracking',
        string='Product with Tracking',
        store=True)
