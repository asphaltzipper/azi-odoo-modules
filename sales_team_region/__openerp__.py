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
    "name": "Sales Team Regions",
    "version": "0.1",
    "summary": "Define sales regions.",
    "category": "Sales",
    "author": "scosist",
    "website": "http://www.github.com/asphaltzipper/azi-odoo-modules",
    'description': """
Define sales team regions (from country groups, countries, and/or states) per sales team. Automatically assign new customers to sales teams given a state. Note: Sales regions may not overlap.
    """,
    "depends": ["crm"],
    "data" : [
        'sales_team_view.xml',
    ],
    "demo": [],
    "test":[],
    "js":[],
    "css":[],
    "installable": True,
    "auto_install": False,
}
