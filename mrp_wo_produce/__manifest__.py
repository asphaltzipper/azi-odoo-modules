# -*- coding: utf-8 -*-
# (c) 2018 Matt Taylor

{
    "name": "Work Order Produce Wizard",
    "version": "12.0.1.0.0",
    "summary": "Wizard for producing/completing Manufacturing Orders with Work Orders",
    "category": "Inventory",
    "author": "Matt Taylor",
    "website": "http://www.github.com/asphaltzipper",
    'description': """
Work Order Produce Wizard
============================
Wizard for completing Manufacturing Orders with Work Orders
1. Check Availability
1. Plan
1. Enter component serial numbers
1. Enter finished good serial numbers
1. Start WO Completion Wizard
   * Enter labor time per work order
   * Click Done to complete all work orders and the manufacturing order
    """,
    "depends": [
        "stock",
        "mrp",
    ],
    "data": [
        'wizard/mrp_wo_produce_views.xml',
        'views/mrp_production_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
