# -*- coding: utf-8 -*-

{
    'license': 'LGPL-3',
    "name": "AZI MRP Product",
    "version": "12.0.1.0.0",
    "author": "Asphalt Zipper",
    "category": "Warehouse",
    "summary": "Create Wizard to display files",
    'description': """
    This module creates a wizard to display files related to product.product or product.template""",
    "website": "http://www.github.com/asphaltzipper",
    "depends": ["azi_mrp"],
    "data": [
        'wizard/compile_product_file_views.xml',
    ],
    "auto_install": False,
    "application": False,
    "installable": True,
}

