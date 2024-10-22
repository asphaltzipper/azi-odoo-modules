# -*- coding: utf-8 -*-
# (c) 2018 Chris Emigh
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "sales_tax_reporting",
    "version": "0.1",
    "summary": "Sales tax Reports",
    "category": "Accounting",
    "author": "Chris Emigh",
    "license": "AGPL-3",
    "website": "http://www.asphaltzipper.com",
    'description': """
Sales Tax Reporting
===================

    """,
    "depends": [
        'account',
        'mrp',
    ],
    'data': [
        'wizard/tax_report_wizard.xml',
    ],
    "installable": True,
    "auto_install": False,
}
