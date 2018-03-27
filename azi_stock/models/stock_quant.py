# -*- coding: utf-8 -*-

from odoo import api, fields, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    category_id = fields.Many2one(
        comodel_name='product.category',
        related='product_id.categ_id',
        readonly=True,
        store=True)
