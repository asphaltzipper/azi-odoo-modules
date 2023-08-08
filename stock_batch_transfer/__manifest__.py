# Copyright (C) 2014 Asphalt Zipper, Inc.
# Author Matt Taylor
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "stock_batch_transfer",
    "version": "16.0.1.0.0",
    "summary": "Stock Batch Transfer",
    "category": "Inventory Control",
    "author": "Matt Taylor",
    'license': 'AGPL-3',
    "website": "https://github.com/asphaltzipper",
    'description': """
Validate a batch of internal transfers
=========================================

* Automatically set done quantity same as required quantity
* Only allow Internal Transfer type.
* Only allow Available pickings.
* Only allow totally incomplete picking lines.
* Skip transfers requiring serial numbers.
* Skip transfers requiring quality checks.
    """,
    "depends": ['quality_control'],
    'data': [
        'views/stock_picking_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}

