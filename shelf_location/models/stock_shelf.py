# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockShelf(models.Model):
    _name = 'stock.shelf'

    name = fields.Char(string='Shelf Location')
    product_count = fields.Integer(string='Product Count', compute='_count')
    inactive_count = fields.Integer(string='Inactive Count', compute='_inactive_count')
    product_ids = fields.Many2many(comodel_name='product.template', string='Products')

    def _count(self):
        for shelf in self:
            shelf.product_count = len(shelf.product_ids)

    def _inactive_count(self):
        for shelf in self:
            shelf.inactive_count = len(shelf.product_ids.filtered(lambda product: product.active))
