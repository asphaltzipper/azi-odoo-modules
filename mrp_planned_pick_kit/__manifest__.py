# Copyright 2020 Matt taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "MRP Planned Pick Kit",
    "summary": "Support kitting for planned manufacturing orders",
    "version": "12.0.1.0.0",
    "category": "Manufacturing",
    "website": "http://www.github.com/asphaltzipper/azi-odoo-modules",
    'description': """
Create and manage picking kits
==============================
    """,
    "author": "mtaylor",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        'stock',
        'mrp',
        'azi_mrp_multi_level',
    ],
    "data": [
        'views/mrp_planned_pick_kit_views.xml',
        'views/product_views.xml',
        'views/mrp_production_views.xml',
        'views/mrp_inventory_views.xml',
        'wizards/production_kit_convert_views.xml',
        'report/report_production_kit_templates.xml',
        'report/report_production_kit.xml',
    ],
}
