# -*- coding: utf-8 -*-

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    added_rm = fields.Boolean(
        string='Added Raw Material',
        required=False,
        help="Raw material added to Manufacturing Order, not on BOM")

    def action_cancel(self):
        for record in self:
            record._action_cancel()
