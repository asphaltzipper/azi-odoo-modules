# Copyright 2020 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "stock_fifo_lot_costing",
    "version": "12.0.1.0.0",
    "summary": "Stock Cost First From Lot, then FIFO",
    "category": "Warehouse",
    "author": "Matt Taylor",
    "license": "AGPL-3",
    "website": "http://www.asphaltzipper.com",
    'description': """
Stock Cost First From Lot, Then FIFO
=======================================

Take the cost of the selected lot, if the product is tracked.  Otherwise, 
perform FIFO costing.
    """,
    "depends": [
        'stock_account',
    ],
    "installable": True,
    "auto_install": False,
    "pre_init_hook": "pre_init_hook",
}
