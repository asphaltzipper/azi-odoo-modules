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
##############################################################################

{
    "name": "Requirements Calculator",
    "version": "0.1",
    "summary": "Material Requirements Calculator",
    "category": "Warehouse Management",
    "author": "scosist",
    "website": "http://www.asphaltzipper.com",
    'description': """
View material requirements for a given product and related bill of materials.
    """,
    "depends": ["product", "stock", "mrp"],
    "data" : [
        'wizard/simulated_pick_view.xml',
        'simulated_pick_product_view.xml',
    ],
    "demo": [],
    "test":[],
    "js":[],
    "css":[],
    "installable": True,
    "auto_install": False,
}
