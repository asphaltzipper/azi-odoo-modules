# -*- coding: utf-8 -*-
# Copyright 2017 Chris Emigh
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "requisition_blanket",
    "version": "10.0.0.1",
    "summary": "Improve Blanket PO Behavior",
    "category": "Purchases",
    "author": "Chris Emigh",
    "license": "AGPL-3",
    "website": "http://www.asphaltzipper.com",
    'description': """
Improve Blanket PO Behavior
===========================

* Create Report for Blanket Orders
* Fix errors in quotations for date to include lead time
* Change available date fields for blanket orders
* Change name sequence prefix from TE to PA
    """,
    "depends": ['purchase_requisition'],
    'data': [
        'data/purchase_requisition_data.yml',
        'report/purchase_agreement_layout.xml',
        'report/blanket_order.xml',
        'views/purchase_requisition_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
