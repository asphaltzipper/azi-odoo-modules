# -*- coding: utf-8 -*-
# (c) 2018 John Welch

{
    "name": "Account Location Tax",
    "version": "10.0.1",
    "summary": "Display sales revenue by zip code",
    "category": "Accounting",
    "author": "John Welch",
    "website": "http://www.github.com/asphaltzipper",
    'description': """
        Breakdown sales revenue by zip + 4
    """,
    'depends' : ['account'],
    "data": [
        'views/location_tax_pivot.xml',
        'security/ir.model.access.csv',
    ],
    "installable": True,
    "auto_install": False,
}
