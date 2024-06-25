# Copyright 2024 Matt taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "MRP Planned Pick Kit",
    "summary": "Support kitting for planned manufacturing orders",
    "version": "16.0.1.0.0",
    "category": "Manufacturing",
    "website": "http://www.github.com/asphaltzipper/azi-odoo-modules",
    'description': """
Create and manage picking kits
==============================

This module was written to support the process of building parts kits for planned manufacturing orders.

We add the following:

* Kits quantity field on product
* Kits quantity field on MRP Inventory record
* Kit form view
* Kit component reports
* Kits assigned/available on Manufacturing Orders
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
        'security/ir.model.access.csv',
        'views/mrp_planned_pick_kit_views.xml',
        'views/product_views.xml',
        'views/mrp_production_views.xml',
        'views/mrp_inventory_views.xml',
        'report/report_production_kit_templates.xml',
        'report/report_production_kit.xml',
    ],
}
