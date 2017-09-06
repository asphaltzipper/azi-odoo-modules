# -*- coding: utf-8 -*-
# Copyright 2017 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "azi_account",
    "version": "0.1",
    "summary": "AZI account Customizations",
    "category": "Accounting",
    "author": "Matt Taylor",
    "license": "AGPL-3",
    "website": "http://www.asphaltzipper.com",
    'description': """
AZI Specialized Customizations to account
=========================================

* Add product to journal entry form view
* Add product to journal item tree view
* Add menu item for account types
* Reformat check
    """,
    "depends": ['account', 'l10n_us_check_printing'],
    'data': [
        'views/account_view_changes.xml',
        'report/azi_print_check.xml',
    ],
    "installable": True,
    "auto_install": False,
}
