# -*- coding: utf-8 -*-

{
    'name': "Procurement Barcode Scanning",
    'summary': "Add barcode scanning facilities to Procurement.",
    'description': """
        This module adds support for barcodes scanning to the Create entry for the procurement.
    """,
    'author': "Bista Solutions",
    'category': 'Usability',
    'version': '1.0',
    'depends': ['barcodes', 'procurement', 'stock'],
    'data': [
        'views/stock_barcode_templates.xml',
        'views/stock_barcode_views.xml',
    ],
    'qweb': [
        "static/src/xml/stock_barcode.xml",
    ],

    'installable': True,
    'application': True,
}
