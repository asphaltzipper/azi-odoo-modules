# -*- coding: utf-8 -*-
# Copyright 2018 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Customer Credit App",
    "version": "10.0.0.0.0",
    "summary": "Customer Credit Application",
    "category": "Sale",
    "author": "Matt Taylor",
    "license": "AGPL-3",
    "website": "http://www.asphaltzipper.com",
    'description': """
Customer Credit Application
===========================

* Add credit_app_date field on res_partner
* Show credit app date on the sales order
    """,
    "depends": ['account', 'sale'],
    'data': [
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
