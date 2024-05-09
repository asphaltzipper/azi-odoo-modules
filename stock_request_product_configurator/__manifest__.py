# -*- coding: utf-8 -*-
{
    "name": "Stock Request Product Configurator",
    "version": "16.0.1.0.0",
    "summary": "Stock Request Configurator",
    "category": "Stock",
    "author": "John Welch",
    "license": "AGPL-3",
    "website": "http://www.github.com/asphaltzipper",
    'description': """
Stock Request Product Configurator
==================================
* Add new button to configure product in stock.request model
    """,
    'depends': ['stock_request_submit', 'product_configurator'],
    "data": [
        'security/ir.model.access.csv',
        'views/stock_request_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
