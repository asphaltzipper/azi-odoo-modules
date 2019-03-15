# -*- coding: utf-8 -*-
# Copyright 2019 Matt taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "MRP Stock Reservation",
    "summary": "Reserve individual stock moves for specified manufacturing orders.",
    "version": "10.0.1.0.0",
    "category": "Manufacturing",
    "website": "http://www.github.com/asphaltzipper/azi-odoo-modules",
    'description': """
        We provide a form view for products where the user can reserve the
        product to one of the waiting manufacturing orders.
    """,
    "author": "mtaylor",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ['mrp', 'mfg_integration', 'product', 'percentage_widget'],
    "data": [
        'views/mfg_work_views.xml',
        'views/product_views.xml',
        'views/product_mrp_reservation_barcode_template.xml',
        'views/mrp_production_views.xml',
    ],
}
