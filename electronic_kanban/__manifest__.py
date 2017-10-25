# -*- coding: utf-8 -*-
# Copyright 2017 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "electronic_kanban",
    "version": "10.0.0.1",
    "summary": "Electronic Kanban",
    "category": "Stock",
    "author": "Matt Taylor",
    "license": "AGPL-3",
    "website": "http://www.asphaltzipper.com",
    'description': """
Electronic Kanban
=================

* Flag products as e-kanban items and set a default kanban quantity (bin size) 
* Manage kanban barcode scan events
* Manually review and create Purchase Orders from kanban scans
    """,
    "depends": ['product', 'stock', 'mrp_mrp'],
    'data': [
        'views/product_views.xml',
        'views/e_kanban_views.xml',
        'views/mrp_material_plan_views.xml',
        'data/e_kanban_sequence.xml',
    ],
    "installable": True,
    "auto_install": False,
}
