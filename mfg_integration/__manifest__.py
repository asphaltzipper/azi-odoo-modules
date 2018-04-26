# -*- coding: utf-8 -*-
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
    ],
    'data': [
        'views/mfg_integration_view.xml',
        'security/ir.model.access.csv',
    ],
    "installable": True,
    "auto_install": False,
}
