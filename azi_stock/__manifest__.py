# -*- coding: utf-8 -*-
# Copyright 2017 Chris Emigh
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "azi_stock",
    "version": "0.1",
    "summary": "AZI Stock Customizations",
    "category": "Warehouse",
    "author": "Chris Emigh",
    "license": "AGPL-3",
    "website": "http://www.asphaltzipper.com",
    'description': """
AZI Specialized Customizations to Stock
=======================================

* Add description to picking move lines
* Show creation date on stock picking tree
    """,
    "depends": ['stock'],
    'data': [
        'views/stock_view_changes.xml',
        'report/transfer_slip.xml',
        'report/product_labels.xml',
        'report/product_report.xml',
        'report/transfer_slip_template.xml',
        'report/stock_quant_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
