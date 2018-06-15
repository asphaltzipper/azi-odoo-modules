# -*- coding: utf-8 -*-
# (c) 2018 Chris Emigh
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "mfg_integration",
    "version": "0.1",
    "summary": "Integrate with Manufacturing Machine Software",
    "category": "Manufacturing",
    "author": "Chris Emigh",
    "website": "http://www.asphaltzipper.com",
    'description': """
Integrate with Manufacturing Machine Software
=============================================

* Raw Material thickness/qty
    """,
    "depends": [
        'product',
        'mrp',
        'stock',
    ],
    'data': [
        'wizards/mfg_create_bom_views.xml',
        'views/product_views.xml',
        'views/product_uom_views.xml',
        'views/workorder_views.xml',
        'data/mfg_integration_data.xml',
        'security/ir.model.access.csv',
    ],
    "installable": True,
    "auto_install": False,
}
