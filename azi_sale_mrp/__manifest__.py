# -*- coding: utf-8 -*-
{
    "name": "AZI Sale MRP",
    "version": "1.0",
    "summary": "SO Phantom Import",
    "category": "Sale",
    "author": "John Welch",
    "license": "AGPL-3",
    "website": "http://www.github.com/asphaltzipper",
    'description': """
AZI Sale MRP
============
* Import phantom BOM in SO lines
    """,
    'depends': [
        'sale_discount_reason',
        'mrp',
    ],
    "data": [
        'security/ir.model.access.csv',
        'wizards/sale_import_phantom_views.xml',
        'views/sale_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
