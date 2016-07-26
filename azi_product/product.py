# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
from openerp.tools.translate import _
import re

# TODO: Add domain on mrp.production.product.line field product_id
#       Add domain on mrp.bom.line field product_id 
#       Investigate bug on domain on purchase.order.line field product_id


# class product_template(osv.Model):
#
#     """
#     store default_code so we can sort tree views
#     """
#
#     _inherit = "product.template"
#     _order = "default_code"
#
#     _columns = {
#         'default_code': fields.related('product_variant_ids', 'default_code', type='char', string='Internal Reference', store=True),
#     }


# class product_product(osv.Model):
#
#     """
#     Enforce unique product code (default_code)
#     Enforce product code formatting
#     Require product code for Stockable products (type='product')
#     TODO: Add produce_ok to product.product
#     TODO: Only require product code on Stockable products when setting purchase_ok, sale_ok, or produce_ok
#     """
#
#     _inherit = "product.product"
#
#     _sql_constraints = [ ('default_code_uniq', 'unique (default_code)', """Product Code must be unique."""), ]
#
#     default_code_pattern = r'^((COPY\.)?[_A-Z0-9-]+\.[A-Z-][0-9])$'
#
#     def _require_default_code(self, cr, uid, ids, context=None):
#         # verify that we have a product code before allowing procurements
#         for product in self.browse(cr, uid, ids, context=context):
#             # require default_code when flagging for sale, purchase, produce
#             if product.type=='product' and not product.default_code and (product.purchase_ok or product.sale_ok):
#                 return False
#         return True
#
#     def _validate_default_code(self, cr, uid, ids, context=None):
#         # require valid default_code, making allowance for copies
#         for product in self.browse(cr, uid, ids, context=context):
#             if product.default_code and not re.match(self.default_code_pattern, product.default_code):
#                 return False
#         return True
#
#     def _validate_default_code_copy(self, cr, uid, ids, context=None):
#         # require completely valid default_code before allowing procurements
#         for product in self.browse(cr, uid, ids, context=context):
#             pattern = r'^COPY\..*$'
#             if product.default_code and re.match(pattern, product.default_code) and (product.purchase_ok or product.sale_ok):
#                 return False
#         return True
#
#     _constraints = [
#         (_require_default_code, 'Stockable product type requires a valid Reference code (default_code field).', ['type','default_code','purchase_ok','sale_ok']),
#         (_validate_default_code, "Reference code (default_code) must match this format: r'" + default_code_pattern + "'", ['default_code']),
#         (_validate_default_code_copy, 'For procurements, copied Reference codes are not allowed', ['type','default_code','purchase_ok','sale_ok']),
#     ]
#
#     def copy(self, cr, uid, id, default=None, context=None):
#         if context is None:
#             context={}
#         product = self.read(cr, uid, id, ['default_code'], context=context)
#         if not default:
#             default = {}
#         default = default.copy()
#         default['default_code'] = _('COPY.') + product['default_code']
#
#         # unset purchase, sale, produce okay flags
#         if product.type == 'product':
#             default['purchase_ok'] = False
#             default['sale_ok'] = False
#             #default['produce_ok'] = False
#
#         return super(product_code_unique_product, self).copy(cr=cr, uid=uid, id=id, default=default, context=context)



class uom_categ_unique(osv.Model):

    """Enforce unique UOM category name"""

    _inherit = 'product.uom.categ'

    _sql_constraints = [ ('name_uniq', 'unique (name)', """Category name must be unique."""), ]

    def copy(self, cr, uid, id, default=None, context=None):
        if context is None:
            context={}

        product = self.read(cr, uid, id, ['name'], context=context)
        if not default:
            default = {}
        default = default.copy()
        default['name'] = product['name'] + _(' (copy)')

        return super(product_uom_categ_unique, self).copy(cr=cr, uid=uid, id=id, default=default, context=context)


class uom_unique(osv.Model):
    
    """Enforce unique UOM name"""
    
    _inherit = 'product.uom'
      
    _sql_constraints = [ ('name_uniq', 'unique (name)', """UOM Name must be unique."""), ]

    def copy(self, cr, uid, id, default=None, context=None):
        if context is None:
            context={}

        product = self.read(cr, uid, id, ['name'], context=context)
        if not default:
            default = {}
        default = default.copy()
        default['name'] = product['name'] + _(' (copy)')

        return super(product_uom_categ_unique, self).copy(cr=cr, uid=uid, id=id, default=default, context=context)




