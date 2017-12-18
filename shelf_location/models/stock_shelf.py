# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class StockShelf(models.Model):
    _name = 'stock.shelf'
    _order = 'name'
    _inherit = ['barcodes.barcode_events_mixin']


    name = fields.Char(
        string='Shelf Name')

    product_count = fields.Integer(
        string='Product Count',
        compute='_count')

    inactive_count = fields.Integer(
        string='Inactive Count',
        compute='_inactive_count')

    product_ids = fields.Many2many(
        comodel_name='product.product',
        string='Products',
        domain=['|', ('active', '=', True), ('active', '=', False)])

    _barcode_scanned = fields.Char(
        string="Barcode Scanned",
        help="Value of the last barcode scanned.",
        store=False)

    def _count(self):
        for shelf in self:
            shelf.product_count = len(shelf.product_ids)

    def _inactive_count(self):
        for shelf in self:
            shelf.inactive_count = len(shelf.product_ids.filtered(lambda product: not product.active))

    @api.model
    def sl_barcode(self, barcode, sl_id):
        shelf = self.env['stock.shelf'].search([('id', '=', sl_id)])
        if not shelf:
            raise UserError(_('No Shelf Found/ so Save!'))
        product_id = self.env['product.product'].with_context(active_test=False).search([('barcode', '=', barcode)])
        shelf.update({'product_ids': [(4, product_id.id)]})

    def button_delete_all(self):
        self.ensure_one()
        self.update({'product_ids': [(6, 0, [])]})
