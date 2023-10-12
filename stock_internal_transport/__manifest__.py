# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP Module
#    
#    Copyright (C) 2023 Asphalt Zipper, Inc.
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
    "name": "stock_internal_transport",
    "version": "16.0.1.1.0",
    "summary": "Stock Internal Transport",
    "category": "Inventory Control",
    "author": "Matt Taylor",
    "license": "AGPL-3",
    "website": "http://www.asphaltzipper.com",
    'description': """
Manage transportation of product on internal transfers
======================================================

Modifies Stock Picking to better manage transportation of product transfers between internal locations.

* Add pickup/delivery addresses
* Add custom picking report
  * Show pickup/delivery addresses
  * Show notes
    """,
    "depends": ['stock'],
    'data': [
        'data/picking_data.xml',
        'views/stock_picking_views.xml',
        'views/res_company_views.xml',
        'report/report_transportdoc.xml',
        'report/picking_reports.xml',
    ],
    "installable": True,
    "auto_install": False,
}
