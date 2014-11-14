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

import openerp.addons.decimal_precision as dp
from openerp import models, fields, api

class simulated_pick_product(models.TransientModel):
    _name = 'simulated.pick.product'

    product_id = fields.Many2one('product.product', 'Product', required=True, ondelete="no action", select=True)
    product_qty = fields.Float('Required Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), required=True)
    on_hand_before = fields.Float('On Hand Before', digits_compute=dp.get_precision('Product Unit of Measure'), required=True)
    on_hand_after = fields.Float('On Hand After', digits_compute=dp.get_precision('Product Unit of Measure'), required=True)
    short = fields.Float('Short', digits_compute=dp.get_precision('Product Unit of Measure'), required=True)
    product_uom = fields.Many2one('product.uom', 'UoM', required=True)
    categ_id = fields.Many2one('product.category', 'Internal Category', required=True)
    route_name = fields.Char('Action', required=True)
    name = fields.Char('Product Name', required=True)
    default_code = fields.Char('Internal Reference', required=True)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
