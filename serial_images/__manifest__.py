# -*- coding: utf-8 -*-
# (c) 2019 Matt Taylor

{
    "name": "Serial Images",
    "version": "10.0.1",
    "summary": "Image Books for Serialized Product Builds",
    "category": "Inventory",
    "author": "Matt Taylor",
    "website": "http://www.github.com/asphaltzipper",
    'description': """
        Upload images and make notes on serial numbered builds
    """,
    "depends": [
        "base",
        "stock",
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/stock_lot_views.xml',
        'views/serial_images_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
