# -*- coding: utf-8 -*-
# (c) 2020 John Welch

{
    "name": "Unmatched Receivers",
    "version": "16.0.1.1.0",
    "summary": "Unmatched Receivers",
    "category": "Purchases",
    "author": "John Welch",
    "license": "AGPL-3",
    "website": "http://www.github.com/asphaltzipper",
    'description': """
Unmatched Receivers
=====================
* Display details about product that is purchased with showing details about journal entries
    """,
    'depends': ['purchase', 'account'],
    "data": [
        'views/purchase_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
