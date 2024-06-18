# -*- coding: utf-8 -*-
{
    "name": "AZI MRP Multi level",
    "version": "16.0.1.0.0",
    "summary": "MRP Inventory",
    "category": "Manufacturing",
    "author": "John Welch",
    "license": "AGPL-3",
    "website": "http://www.github.com/asphaltzipper",
    "description": """
AZI MRP Multi Level
===================
* Modified mrp.inventory to have routing details of the product
    """,
    "depends": [
        'mrp_multi_level',
        'web_notify',
        'stock_request_schedule',
        'electronic_kanban',
        'mfg_integration',
        'purchase_requisition',
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/mrp_inventory_views.xml',
        'views/material_plan_log_views.xml',
        'views/product_mrp_area_views.xml',
        'views/mrp_planned_order_views.xml',
        'wizards/mrp_multi_level_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
