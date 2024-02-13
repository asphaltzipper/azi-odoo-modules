# -*- coding: utf-8 -*-

{
    'license': 'LGPL-3',
    "name": "AZI Stock Request Kanban",
    "version": "16.0.1.1.0",
    "author": "Asphalt Zipper",
    "category": "Extra Tools",
    "summary": "Modify Kanban Report",
    'description': """
    This module modify kanban report.""",
    "website": "http://www.github.com/asphaltzipper",
    "depends": [
        "stock_request_kanban",
        "azi_stock",
        "barcode_font",
    ],
    "data": [
        'report/stock_request_kanban_template.xml',
    ],
    "auto_install": False,
    "application": False,
    "installable": True,
}

