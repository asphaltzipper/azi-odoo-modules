# -*- coding: utf-8 -*-

from odoo import models, fields


class StockShelf(models.Model):
    _inherit = 'stock.shelf'

    deprecated_count = fields.Integer(
        string='Deprecated Count',
        compute='_deprecated_count')

    def _deprecated_count(self):
        for shelf in self:
            shelf.deprecated_count = len(shelf.product_ids.filtered(lambda product: product.deprecated))
