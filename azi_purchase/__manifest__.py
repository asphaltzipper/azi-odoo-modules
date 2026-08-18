# -*- coding: utf-8 -*-
# Copyright 2017 Chris Emigh
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "azi_purchase",
    "version": "1.0",
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
        'data/mail_template_data.xml',
        'views/purchase_views.xml',
        'reports/purchase_order_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'azi_purchase/static/src/js/purchase_line_product_field.js',
        ],
    },
    "installable": True,
    "auto_install": False,
}
