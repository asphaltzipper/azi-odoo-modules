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
* Create a new turnover report 
    """,
    'depends': [
        'stock_account',
    ],
    "data": [
        'security/ir.model.access.csv',
        'report/inventory_turnover_report.xml',
    ],
    "installable": True,
    "auto_install": False,
}
