# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP Module
#    
#    Copyright (C) 2017 Asphalt Zipper, Inc.
#    Author Matt Taylor

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
    "name": "engineering_product",
    "version": "0.1",
    "summary": "Engineering Features for Products",
    "category": "Engineering",
    "author": "Matt Taylor",
    "website": "http://www.asphaltzipper.com",
    'description': """
Engineering Features for Products
=================================

* Require Unique Product Code (product.default_code)
* Create eng code sequence
* Create engineering categories
* Add engineering code and revision fields
* Constrain eng code format (using regular expression)
* Add Deprecated field
    """,
    "depends": [
        'product',
        'stock',
        'electronic_kanban',
        'shelf_location',
    ],
    'data': [
        'data/product_data.xml',
        'views/product_views.xml',
        'views/shelf_location_views.xml',
        'views/engineering_category_views.xml',
        'views/e_kanban_views.xml',
        'views/eng_coating.xml',
        'security/ir.model.access.csv',
    ],
    "installable": True,
    "auto_install": False,
}
