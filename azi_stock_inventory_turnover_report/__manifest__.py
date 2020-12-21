# -*- coding: utf-8 -*-
{
    "name": "AZI Stock Inventory Turnover Report",
    "version": "12.0.1.0.0",
    "summary": "turnover report",
    "category": "Warehouse",
    "author": "John Welch",
    "website": "http://www.github.com/asphaltzipper",
    'description': """
AZI Stock Inventory Turnover Report
===================================
* Create a new turnover report and fixing bug in oca module
    """,
    'depends': [
        'stock_inventory_turnover_report',
    ],
    "data": [
        'views/product_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
