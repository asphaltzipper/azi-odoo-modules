# -*- coding: utf-8 -*-
from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    shelf_ids = fields.Many2many(
        comodel_name='stock.shelf',
        string="Stock Shelves", copy=False)
