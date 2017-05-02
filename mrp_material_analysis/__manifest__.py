# -*- coding: utf-8 -*-
# Copyright 2017 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "MRP Material Analysis",
    "summary": "Determine incomplete transactions based on stock moves and a master schedule given a product.",
    "version": "10.0.1.0.0",
    "category": "Manufacturing",
    "website": "http://www.github.com/asphaltzipper/azi-odoo-modules",
    'description': "Determine imcomplete transactions for a given product.",
    "author": "scosist",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["mrp_master_schedule"],
    "data": [
        'security/ir.model.access.csv',
        'views/mrp_material_analysis_line_view.xml',
        'wizards/mrp_material_analysis_view.xml',
    ],
    "demo": [
    ],
}
