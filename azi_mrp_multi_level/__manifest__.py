# -*- coding: utf-8 -*-
{
    "name": "AZI MRP Multi level",
    "version": "12.0.1.0.0",
    "summary": "MRP Inventory",
    "category": "Manufacturing",
    "author": "John Welch",
    "website": "http://www.github.com/asphaltzipper",
    'description': """
AZI MRP Multi Level
===================
* Modified mrp.inventory to have routing details of the product
    """,
    'depends': ['mrp_multi_level', 'web_notify'],
    "data": [
        'security/ir.model.access.csv',
        'views/mrp_inventory_views.xml',
        'views/material_plan_log_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
