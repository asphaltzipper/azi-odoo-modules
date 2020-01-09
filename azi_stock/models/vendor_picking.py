# -*- coding: utf-8 -*-
# Copyright 2017 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    supplier_codes = fields.Char(
        compute='_compute_supplier_codes')

    def _compute_supplier_codes(self):
        for rec in self:
            rec.supplier_codes = ", " .join(rec.product_id.seller_ids.filtered(lambda r: r.product_code).mapped('product_code'))
