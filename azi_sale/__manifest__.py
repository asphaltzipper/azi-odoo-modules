# -*- coding: utf-8 -*-
# Copyright 2017 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "azi_sale",
    "version": "0.1",
    "summary": "AZI Sales Customizations",
    "category": "Sales",
    "author": "Scott Saunders",
    "license": "AGPL-3",
    "website": "http://www.asphaltzipper.com",
    'description': """
AZI Specialized Customizations to Sales
=======================================

* Filter invoice and delivery addresses by partner on the sales order
* Add contractors and municipality filters to the crm team search view
    """,
    "depends": ['sale', 'crm', 'sales_team_industry'],
    'data': [
        'views/crm_team_view.xml',
        'views/sale_order_view.xml',
    ],
    "installable": True,
    "auto_install": False,
}
