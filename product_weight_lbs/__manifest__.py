# -*- coding: utf-8 -*-
# Copyright 2017 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "product_weight_lbs",
    "summary": "Product weight in lbs",
    "version": "12.0.1.0.0",
    "category": "Sales",
    "website": "http://www.github.com/asphaltzipper/azi-odoo-modules",
    "author": "scosist",
    "license": "AGPL-3",
    'description': """
Product Weight and Shipping Weight in lbs
=========================================

* Add weight_in_lbs field to product.product and product.template
* Modify product weight field to read only
    * Compute from weight_in_lbs and store value
* Add weight_in_lbs and shipping_weight_in_lbs fields to stock.picking and stock.quant.package
    """,
    "installable": True,
    "depends": ['product', 'stock', 'delivery'],
    'data': [
        'views/product_product_view.xml',
        'views/product_template_view.xml',
        'views/stock_picking_view.xml',
        'views/stock_quant_package_view.xml',
        'data/product_data.xml',
    ],
}
