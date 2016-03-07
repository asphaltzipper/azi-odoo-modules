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
    "name": "MRP Time Bucket",
    "version": "0.1",
    "summary": "Implement MRP time buckets.",
    "category": "Manufacturing",
    "author": "scosist",
    "website": "http://www.github.com/asphaltzipper/azi-odoo-modules",
    'description': """
        Schedule delivery of supplies to correspond with demand dates.

        Use daily or weekly time buckets to generate an order at the latest possible date.

        Note: this module is not compatible with the Calendars on Orderpoints (stock_calendar) module.
    """,
    "depends": ["mrp"],
    "data" : [
#        'mrp_time_bucket_view.xml',
    ],
    "demo": [],
    "test":[],
    "js":[],
    "css":[],
    "installable": True,
    "auto_install": False,
}
