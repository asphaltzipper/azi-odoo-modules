# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import re

# TODO: Add domain on mrp.production.product.line field product_id
#       Add domain on mrp.bom.line field product_id 
#       Investigate bug on domain on purchase.order.line field product_id


class ProductTemplate(models.Model):
    """
        Add product manager field
        Add default proc field
    """
    _inherit = "product.template"

    product_manager = fields.Many2one('res.users', 'Product Manager')

    default_proc_qty = fields.Float(related='product_variant_ids.default_proc_qty')


class ProductProduct(models.Model):
    """
    Enforce unique product code (default_code)
    Enforce product code formatting
    Require product code for Stockable products (type='product')
    TODO: Add produce_ok to product.product and constrain when setting this field
    """

    _inherit = "product.product"

    _sql_constraints = [('default_code_uniq', 'unique (default_code)', "Product Code must be unique."), ]

    default_proc_qty = fields.Float(
        string='Procurement Qty',
        help="Default order quantity when requesting procurements by barcode scanning")

    default_code_pattern = r'^((COPY\.)?[_A-Z0-9-]+\.[A-Z-][0-9])$'

    @api.constrains('type', 'default_code', 'purchase_ok', 'sale_ok')
    def _require_default_code(self):
        # verify that we have a product code before allowing procurements
        for product in self:
            # require default_code when flagging for sale, purchase, produce
            if product.type == 'product' and not product.default_code and (product.purchase_ok or product.sale_ok):
                raise ValidationError(_('Stockable product type requires a valid Reference code (default_code field).'))
        return True

    @api.constrains('default_code')
    def _validate_default_code(self):
        # require valid default_code, making allowance for copies
        for product in self:
            if product.type in ('consu', 'product'):
                if product.default_code and not re.match(self.default_code_pattern, product.default_code):
                    raise ValidationError(_('Reference code (default_code) must match this format:') + " r'%s'" % self.default_code_pattern)
        return True

    @api.constrains('type', 'default_code', 'purchase_ok', 'sale_ok')
    def _validate_default_code_copy(self):
        # require completely valid default_code before allowing procurements
        for product in self:
            pattern = r'^COPY\..*$'
            if product.default_code and re.match(pattern, product.default_code) and (product.purchase_ok or product.sale_ok):
                raise ValidationError(_('For procurements, copied Reference codes are not allowed.'))
        return True

    @api.one
    def copy(self, default=None):
        product = self
        if default is None:
            default = {}
        default = default.copy()
        default['default_code'] = _('COPY.') + product['default_code']
        # unset purchase, sale, produce okay flags
        if product.type == 'product':
            default['purchase_ok'] = False
            default['sale_ok'] = False
            # default['produce_ok'] = False
        return super(ProductProduct, self).copy(default=default)


class ProductUomCategory(models.Model):
    """Enforce unique UOM category name"""

    _inherit = 'product.uom.categ'

    _sql_constraints = [('name_uniq', 'unique (name)', """Category name must be unique."""), ]

    @api.multi
    def copy(self, default=None):
        if not default:
            default = {}
        default = default.copy()
        default['name'] = self.name + _(' (copy)')

        return super(ProductUomCategory, self).copy(default=default)


class ProductUom(models.Model):
    """Enforce unique UOM name"""

    _inherit = 'product.uom'

    _sql_constraints = [('name_uniq', 'unique (name)', """UOM Name must be unique."""), ]

    @api.multi
    def copy(self, default=None):
        if not default:
            default = {}
        default = default.copy()
        default['name'] = self.name + _(' (copy)')

        return super(ProductUom, self).copy(default=default)
