# -*- coding: utf-8 -*-
# © 2016 Scott Saunders - Asphalt Zipper, Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "MRP BOM Effectivity",
    "summary": "On BOM lookup, allow comparison of BOM effectivity date",
    "version": "9.0.1.0.0",
    "category": "Manufacturing",
    "website": "https://github.com/asphaltzipper/azi-odoo-modules",
    "author": "scosist",
    "depends": ["mrp", "purchase", "sale_order_dates"],
    "license": "AGPL-3",
    "data": [
        "views/mrp_production_view.xml",
    ],
    "installable": False,
    "auto_install": False,
}
