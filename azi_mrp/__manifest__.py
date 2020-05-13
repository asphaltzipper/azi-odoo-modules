# -*- coding: utf-8 -*-
# Copyright 2017 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "azi_mrp",
    "version": "12.0.1.0.0",
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
* Change repair order account move names to the name of the repair order
    """,
    "depends": ['stock', 'mrp', 'shelf_location'],
    'data': [
        'views/mrp_view_changes.xml',
        'report/mrp_report.xml',
        'report/mrp_production_templates.xml',
        'views/production_move_analysis.xml',
        'security/ir.model.access.csv',
    ],
    "installable": True,
    "auto_install": False,
}
