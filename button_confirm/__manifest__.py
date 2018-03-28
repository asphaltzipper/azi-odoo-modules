# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "button_confirm",
    "version": "0.1",
    "summary": "Confirm before archiving",
    "category": "General",
    "author": "Chris Emigh",
    "license": "AGPL-3",
    "website": "http://www.asphaltzipper.com",
    'description': """
Confirm before archiving
=======================================

* Add Confirm button before archiving
    """,
    "depends": ['sale', 'product', 'mrp', 'stock'],
    'data': [
        'views/confirm.xml',
    ],
    "installable": True,
    "auto_install": False,
}
