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

import datetime
from openerp import models, fields, api
from openerp.tools.translate import _

class procurement_order(models.Model):
    _inherit = 'procurement.order'

    @api.model
    def _procure_orderpoint_confirm(self, use_new_cursor=False, company_id = False):
        then = datetime.datetime.now()
        bom_obj = self.env['mrp.bom']
        bom_obj.compute_llc()
        #for prod_id in product_ids:
#            product = product_obj.browse(cr, uid, prod_id)
            #bom_id = bom_obj._bom_find(cr, uid, product_uom=product.product_tmpl_id.uom_id.id, product_id=product.id)
#            bom_id = bom_obj._bom_find(cr, uid, product_id=product.id)
            #top level boms only

#            if bom_id:
#                bom_point = bom_obj.browse(cr, uid, bom_id)
#                bom_obj._bom_explode_llc(cr, uid, bom_point, product, context=context)
#            else:
#                product_obj._set_llc(cr, uid, product.id, 0, context=context)
        if use_new_cursor:
            self._cr.commit()
        now = datetime.datetime.now()
        #import pdb
        #pdb.set_trace()
        return super(procurement_order, self)._procure_orderpoint_confirm(use_new_cursor, company_id)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
