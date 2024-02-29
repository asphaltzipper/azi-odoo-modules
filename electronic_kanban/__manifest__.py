# Copyright 2017 Scott Saunders
# Copyright 2020 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "electronic_kanban",
    "version": "12.0.1.0.0",
    "summary": "Electronic Kanban",
    "category": "Stock",
    "author": "Matt Taylor",
    "license": "AGPL-3",
    "website": "http://www.asphaltzipper.com",
    'description': """
Electronic Kanban Integration
=============================

Products
--------
* Flag products for e-kanban management
* Show computed e-kanban summary data on the product
* Add header button to show kanbans for this product

E-Kanban
--------
* Add Obsolete field (product deprecated) to Kanban objects
* Add Product Active field to Kanban objects
* Add Manager field (product responsible user) to Kanban objects

Shelf Location
--------------
* Provide the ability to scan kanban cards to add product to a shelf location
    """,
    "depends": [
        'stock',
        'shelf_location',
        'stock_request',
        'azi_stock_request_kanban',
        'engineering_product',
        'stock_inventory',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
        'views/stock_request_views.xml',
        'views/stock_request_order_views.xml',
        'views/stock_request_kanban_views.xml',
        'wizard/wizard_stock_kanban_inventory_product_views.xml',
        'views/stock_inventory_kanban_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
