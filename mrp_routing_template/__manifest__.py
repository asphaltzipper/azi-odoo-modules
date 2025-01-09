# Copyright (C) 2025 Asphalt Zipper, Inc.
# Author Matt Taylor
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "mrp_routing_template",
    "version": "16.0.1.0.0",
    "summary": "MRP Routing Templates",
    "category": "Manufacturing",
    "author": "Matt Taylor",
    "license": "AGPL-3",
    "website": "http://www.asphaltzipper.com",
    'description': """
MRP Routing Templates
=========================================

* Workcenter routing templates with sequence
* Used to apply a standard routing on BOM Operations
    """,
    "depends": ['mrp'],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_routing_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
