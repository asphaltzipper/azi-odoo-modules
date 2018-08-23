# -*- coding: utf-8 -*-
# (c) 2018 Matt Taylor
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Merge Manufacturing Orders",
    "version": "1.0",
    "description": "Merge Manufacturing Orders",
    "summary": "Merge Manufacturing Orders",
    "category": "Manufacturing",
    "author": "mtaylor",
    "website": "http://www.github.com/asphaltzipper/azi-odoo-modules",
    "depends": [
        "mrp",
    ],
    "data": [
        "wizards/mrp_production_merge_views.xml",
    ],
    "installable": True,
    "auto_install": False,
}
