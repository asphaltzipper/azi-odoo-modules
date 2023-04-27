# -*- coding: utf-8 -*-
{
    "name": "AZI Product Exception",
    "version": "1.0",
    "summary": "Receipt Warning",
    "category": "Warehouse",
    "author": "John Welch",
    "license": "AGPL-3",
    "website": "http://www.github.com/asphaltzipper",
    'description': """
AZI Product Exception
=====================
* Handle product receipt warning
    """,
    'depends': [
        'stock',
    ],
    "data": [
        'views/product_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
