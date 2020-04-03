# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class StockShelf(models.Model):
    _name = 'stock.shelf'
    _description = 'Stock Shelf'
    _order = 'name'

    _sql_constraints = [('name_uniq', 'unique (name)', "Name must be unique")]

    name = fields.Char(
        string='Shelf Name',
        required=True)

    product_count = fields.Integer(
        string='Product Count',
        compute='_count')

    inactive_count = fields.Integer(
        string='Inactive Count',
        compute='_inactive_count')

    product_ids = fields.Many2many(
        comodel_name='product.template',
        string='Products',
        domain=['|', ('active', '=', True), ('active', '=', False)])

    _barcode_scanned = fields.Char(
        string="Barcode Scanned",
        help="Value of the last barcode scanned.",
        store=False)

    @api.constrains('name')
    def _validate_name_chars(self):
        if self.name:
            invalid_chars = [" ", "\t", "\n", "\r", "\f"]
            if any(char in self.name for char in invalid_chars):
                raise ValidationError("Shelf names can't white space (spaces, tabs, etc)")
        return True

    def _count(self):
        for shelf in self:
            shelf.product_count = len(shelf.product_ids)

    def _inactive_count(self):
        for shelf in self:
            shelf.inactive_count = len(shelf.product_ids.filtered(lambda product: not product.active))

    def button_delete_all(self):
        self.ensure_one()
        self.update({'product_ids': [(6, 0, [])]})
