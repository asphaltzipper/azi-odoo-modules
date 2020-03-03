# -*- coding: utf-8 -*-
# Copyright 2020 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "mrp_electronic_kanban",
    "version": "10.0.0.1",
    "summary": "MRP Electronic Kanban",
    "category": "Stock",
    "author": "Matt Taylor",
    "license": "AGPL-3",
    "website": "https://github.com/asphaltzipper",
    'description': """
MRP Planning for Electronic Kanban
==================================

* Add e-kanban field to MRP Material Plan view
    """,
    "depends": ['electronic_kanban', 'mrp_mrp'],
    'data': [
        'views/mrp_material_plan_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
