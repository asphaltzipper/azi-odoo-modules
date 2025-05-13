# Copyright 2017 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "BOM Structure Viewer",
    "version": "16.0.1.0.0",
    "summary": "Fast Multi-Level Bill of Materials Views",
    "category": "Manufacturing",
    "author": "Matt Taylor",
    "license": "AGPL-3",
    "website": "http://www.asphaltzipper.com",
    "description": """
Bom Structure Viewer
====================

* Show Bom Structure with links
    """,
    "depends": ["mrp", "stock"],
    "data": [
        "views/stock_lot_views.xml",
        "report/mrp_bom_structure_templates.xml",
    ],
    "installable": True,
    "auto_install": False,
}
