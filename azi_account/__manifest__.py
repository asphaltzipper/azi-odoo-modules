# -*- coding: utf-8 -*-
# Copyright 2017 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "azi_account",
    "version": "12.0.1.0.0",
    "summary": "AZI account Customizations",
    "category": "Accounting",
    "author": "Matt Taylor",
    "license": "AGPL-3",
    "website": "http://www.asphaltzipper.com",
    'description': """
AZI Specialized Customizations to account
=========================================

* Show product on journal entry form view
* Show product on journal item tree view
* Add fields on reconciliation form
    * Analytic Tags
    * Product
* Add Receipt on File field to journal item
* Add menu item for account types
* Reformat check
    """,
    "depends": ['account_check_printing', 'account_move_line_product', 'taxjar_integration_ts', 'sale'],
    'data': [
        'views/account.xml',
        'views/account_view_changes.xml',
        'views/account_move_line_views.xml',
        'views/account_invoice_views.xml',
        'views/account_config_settings_views.xml',
        'report/report_invoice.xml',
    ],
    'qweb': [
        'views/account_reconciliation_template.xml',
    ],
    "installable": True,
    "auto_install": False,
}
