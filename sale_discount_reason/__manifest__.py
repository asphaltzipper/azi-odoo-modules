# -*- coding: utf-8 -*-
# Copyright 2017 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "sale_discount_reason",
    "version": "1.0",
    "summary": "Sale Discount Reason",
    "category": "Sales",
    "author": "Matt Taylor",
    "license": "AGPL-3",
    "website": "http://www.asphaltzipper.com",
    "description": """
Explanations For Sales Discounts
================================

Choose a reason for discounting a Sales Order Line
    """,
    "depends": ['sale', 'sale_margin'],
    "data": [
        'views/sale_discount_reason_views.xml',
        'security/ir.model.access.csv',
    ],
    "installable": True,
    "auto_install": False,
}
