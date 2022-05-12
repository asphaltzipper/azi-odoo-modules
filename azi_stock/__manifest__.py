# -*- coding: utf-8 -*-
# Copyright 2017 Chris Emigh
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "azi_stock",
    "version": "12.0.1.0.0",
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
* Prevent negative quants for serial tracked products
    """,
    "depends": [
        'stock',
        'purchase',
        'engineering_product',
        'shelf_location',
        'stock_inventory_valuation_location',
        'barcode_font',
    ],
    'data': [
        'views/stock_view_changes.xml',
        'views/stock_move_line_views.xml',
        'report/transfer_slip_template.xml',
        'report/transfer_slip.xml',
        'report/product_labels.xml',
        'report/product_report.xml',
        'report/stock_quant_views.xml',
        'report/picking_report.xml',
        # 'report/location_labels.xml',
        # 'report/location_report.xml',
        'report/transfer_slip_template.xml',
        'report/stock_quant_report.xml',
        'report/stock_report.xml',
        'views/stock_quant_views.xml',
        'views/stock_inventory_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
