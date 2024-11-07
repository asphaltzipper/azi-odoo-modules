# -*- coding: utf-8 -*-
# (c) 2024 John Welch

{
    "name": "AZI Stock Request Purchase",
    "version": "16.0.1.0.0",
    "summary": " Stock request, purchase",
    "category": "Warehouse Management",
    "author": "John Welch",
    "license": "LGPL-3",
    "website": "http://www.github.com/asphaltzipper",
    "description": """
AZI Stock Request Purchase
=====================
* Add some features in the stock.request.order
    """,
    "depends": ["electronic_kanban", "stock_request_purchase"],
    "data": [
        "views/stock_request_order_views.xml",
    ],
    "installable": True,
    "auto_install": False,

}
