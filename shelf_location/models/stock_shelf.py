# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class StockShelf(models.Model):
    _name = 'stock.shelf'
    _order = 'name'
    _inherit = ['barcodes.barcode_events_mixin']

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

    def _find_product_from_barcode(self, barcode):
        """
        Method to be inherited and extended for finding products from alternate barcoded objects
        :param barcode: string from barcode scan
        :return: product
        """
        return self.env['product.template'].with_context(active_test=False).search(
            ['|', ('barcode', '=', barcode), ('default_code', '=', barcode)])

    def on_barcode_scanned(self, barcode):
        shelf = self.env['stock.shelf'].search([('id', '=', self.id)])
        if not shelf:
            raise UserError(_('No Shelf Found/ so Save!'))
        product = self._find_product_from_barcode(barcode)
        if product:
            shelf.update({'product_ids': [(4, product.id)]})
        else:
            self.env.user.notify_warning(message=barcode, title="Unknown Barcode", sticky=True)

    def button_delete_all(self):
        self.ensure_one()
        self.update({'product_ids': [(6, 0, [])]})
