# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP Module
#
# Author: Scott Saunders. Copyright Asphalt Zipper, Inc.
# Contributors: Matt Taylor
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
    "name": "Purchase Line Delivery",
    "version": "10.0.0",
    "summary": "Purchase Order Line delivery method",
    "category": "Purchases",
    "author": "mtaylor",
    "website": "http://www.github.com/asphaltzipper/azi-odoo-modules",
    'description': """
        Add a field on purchase order line for specifying a delivery method.
    """,
    "depends": ["purchase"],
    "data": [
        'views/purchase_views.xml',
        'report/templates.xml',
    ],
    "installable": True,
    "auto_install": False,
}
