# -*- coding: utf-8 -*-
# Copyright 2017 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "azi_mrp_repair",
    "version": "12.0.1.0.0",
    "summary": "AZI MRP Repair Customizations",
    "category": "Manufacturing",
    "author": "Matt Taylor",
    "license": "AGPL-3",
    "website": "http://www.asphaltzipper.com",
    'description': """
AZI Specialized Customizations to MRP Repair
============================================

* Change repair order account move names to the name of the repair order
* Show repaired serial number in list view
    """,
    "depends": ['repair', 'stock_inventory_revaluation'],
    'data': [
        'views/mrp_repair_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
