# -*- coding: utf-8 -*-
# Copyright 2017 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "azi_mrp",
    "version": "10.0.0.1",
    "summary": "AZI MRP Customizations",
    "category": "Manufacturing",
    "author": "Matt Taylor",
    "license": "AGPL-3",
    "website": "http://www.asphaltzipper.com",
    'description': """
AZI Specialized Customizations to MRP
=====================================

* Show stock moves button on MO form
* Add serial-required column to raw material list for sorting
    """,
    "depends": ['stock'],
    'data': [
        'views/mrp_view_changes.xml',
    ],
    "installable": True,
    "auto_install": False,
}
