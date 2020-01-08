# -*- coding: utf-8 -*-
# Copyright 2017 Chris Emigh
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "azi_purchase",
    "version": "12.0.1.1.0",
    "summary": "AZI Purchase",
    "category": "Stock",
    "author": "Chris Emigh",
    "license": "AGPL-3",
    "website": "http://www.asphaltzipper.com",
    'description': """
AZI Purchase
============

* Set a sent date for emails
* Filter Tree by [not]sent
    """,
    "depends": ['purchase'],
    'data': [
        'views/purchase_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
