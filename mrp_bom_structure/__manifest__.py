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
Bom Structure Viewer
=====================================

* Show Bom Structure with links
    """,
    "depends": ['mrp'],
    'data': [
        'report/mrp_bom_structure_templates.xml',
    ],
    "installable": True,
    "auto_install": False,
}