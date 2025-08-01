# -*- coding: utf-8 -*-
{
    "name": "AZI MRP BOM History",
    "version": "16.0.1.1.0",
    "summary": "BOM History",
    "category": "Manufacturing",
    "author": "John Welch",
    "license": "AGPL-3",
    "website": "http://www.github.com/asphaltzipper",
    "description": """
AZI MRP BOM History
===================
* Create a new model for BOM History
    """,
    "depends": [
        'mrp',
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/mrp_bom_history_views.xml',
        'reports/mrp_bom_history_report.xml',
        'reports/mrp_report.xml',
    ],
    "installable": True,
    "auto_install": False,
}
