# -*- coding: utf-8 -*-
{
    "name": "AZI Sale Account",
    "version": "16.0.1.0.0",
    "summary": "Customer Invoice Service",
    "category": "Accounting",
    "author": "John Welch",
    "license": "AGPL-3",
    "website": "http://www.github.com/asphaltzipper",
    'description': """
AZI Sale Account
================
* Create a customer service report
    """,
    'depends': [
        'sale_margin',
    ],
    "data": [
        'security/ir.model.access.csv',
        'reports/account_service_profit_report.xml',
    ],
    "installable": True,
    "auto_install": False,
}
