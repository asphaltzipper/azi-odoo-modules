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
    "name": "engineering_bom",
    "version": "12.0.1.1.0",
    "summary": "Engineering Bills of Materials Management",
    "category": "Engineering",
    "author": "Matt Taylor",
    "website": "http://www.asphaltzipper.com",
    'description': """
Engineering Bills of Materials Management
=========================================

* BOM import with versions
* Tools for updating mrp BOMs from imported BOMs
    """,
    "depends": [
        'mrp',
        'mfg_integration',
        'ecm',
        'product_configurator',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/import_engineering_bom_views.xml',
        'views/engineering_bom_views.xml',
        'views/engineering_diff_views.xml',
        'views/engineering_bom_batch_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
