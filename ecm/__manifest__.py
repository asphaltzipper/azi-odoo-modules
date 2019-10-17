# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP Module
#    
#    Copyright (C) 2019 Asphalt Zipper, Inc.
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
    "name": "ecm",
    "version": "0.1",
    "summary": "Engineering Change Management",
    "category": "Engineering",
    "author": "Matt Taylor",
    "website": "http://www.asphaltzipper.com",
    'description': """
Manage Engineering Changes to Products
======================================

* Select products to be revised
* Attach change drawings
* Request/Require sign-off
* Create the new product revisions
* Compare BOMs between old and new versions
* List all revisions on each product
    """,
    "depends": [
        'stock',
        'mrp',
        'engineering_product',
    ],
    'data': [
        'data/ecm_eco_data.xml',
        'wizards/upload_line_doc_views.xml',
        'views/ecm_views.xml',
        'views/product_views.xml',
        'wizards/approval_sign_views.xml',
        'security/security_data.xml',
        'security/ir.model.access.csv',
    ],
    "installable": True,
    "auto_install": False,
}
