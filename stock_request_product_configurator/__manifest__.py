# -*- coding: utf-8 -*-
{
    "name": "Stock Request Product Configurator",
    "version": "12.0.1.0.0",
    "summary": "Stock Request Configurator",
    "category": "Stock",
    "author": "John Welch",
    "website": "http://www.github.com/asphaltzipper",
    'description': """
Stock Request Product Configurator
==================================
* Add new button to configure product in stock.request model
    """,
    'depends': ['stock_request_submit', 'product_configurator'],
    "data": [
        'views/stock_request_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
