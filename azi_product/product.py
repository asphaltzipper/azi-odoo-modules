# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
from openerp.tools.translate import _


class product_code_unique_product(osv.Model):
    
    """Require unique product code (default_code)"""
    
    _inherit = "product.product"
      
    _columns = {
        'default_code':  fields.char('Reference', size=64, required=True),
    }
    
    _sql_constraints = [ ('default_code_uniq', 'unique (default_code)', """Product Code must be unique."""), ]

    def copy(self, cr, uid, id, default=None, context=None):
        if context is None:
            context={}

        product = self.read(cr, uid, id, ['default_code'], context=context)
        if not default:
            default = {}
        default = default.copy()
        default['default_code'] = product['default_code'] + _(' (copy)')

        return super(product_code_unique_product, self).copy(cr=cr, uid=uid, id=id, default=default, context=context)



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




