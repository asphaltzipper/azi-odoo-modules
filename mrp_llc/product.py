# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP Module
#    
#    Copyright (C) 2014 Asphalt Zipper, Inc.
#    Author scosist
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from openerp import models, fields, api
from openerp.tools.translate import _

class product_product(models.Model):
    _inherit = "product.product"

    low_level_code = fields.Integer('LLC', required=True, default=0)
    
#    @api.multi
#    def _get_llc(self, id):
#        return self.browse(id).low_level_code

#    @api.multi
    #def _set_llc(self, id, llc):
#    def _set_llc(self, llc):
        #current_llc = self._get_llc(id)
        #if llc > current_llc:
#        if llc > self.low_level_code:
#            self.write({'low_level_code': llc})
            #self.write([id], {'low_level_code': llc})
            #for prod in self:
            #    prod.write({'low_level_code': llc})

#    def write(self, cr, uid, ids, vals, context=None):
#        import pdb
#        pdb.set_trace()
#        return super(product_product, self).write(cr, uid, ids, vals, context=context)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
