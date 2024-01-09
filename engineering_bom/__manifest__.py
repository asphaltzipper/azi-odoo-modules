# Copyright (C) 2023 Asphalt Zipper, Inc.
# Author Matt Taylor
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "engineering_bom",
    "version": "16.0.1.0.0",
    "summary": "Engineering Bills of Materials Management",
    "category": "Engineering",
    "author": "Matt Taylor",
    "license": "AGPL-3",
    "website": "http://www.asphaltzipper.com",
    'description': """
Engineering Bills of Materials Management
=========================================

* BOM import with versions
* Tools for updating mrp BOMs from imported BOMs
    """,
    "depends": [
        'mrp',
        'mfg_integration',
        'ecm',
        'product_configurator',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/import_engineering_bom_views.xml',
        'views/engineering_bom_views.xml',
        'views/engineering_diff_views.xml',
        'views/engineering_bom_batch_views.xml',
        'views/product_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
