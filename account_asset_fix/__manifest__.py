# -*- coding: utf-8 -*-
# Copyright 2017 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "account_asset_fix",
    "version": "0.1",
    "summary": "Fixed Asset Improvements",
    "category": "Accounting",
    "author": "Matt Taylor",
    "license": "AGPL-3",
    "website": "http://www.asphaltzipper.com",
    'description': """
Fixed Asset Improvements
========================

* Show menu item Generate Asset Entries
* Change wizard behavior
    * Date journal entries same as the date specified by the user
    * Give the user the option to post journal entries
    """,
    "depends": ['account_asset'],
    'data': [
        'wizard/asset_depreciation_confirmation_wizard_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
