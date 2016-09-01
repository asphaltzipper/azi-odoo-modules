# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP Module
#    
#    Copyright (C) 2014 Asphalt Zipper, Inc.
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
    "name": "azi_product",
    "version": "0.1",
    "summary": "AZI Product Customizations",
    "category": "Inventory Control",
    "author": "Matt Taylor",
    "website": "http://www.asphaltzipper.com",
    'description': """
AZI Specialized Customizations to Product
=========================================

* Require Unique Product Code (product.default_code)
* Require Unique UOM Category Name
* Require Unique UOM Name
* Rename, create, inactivate some UOMs and UOM Categories
    """,
    "depends": ["product"],
    'data': ['views/product_views.xml', ],
    "installable": True,
    "auto_install": False,
}