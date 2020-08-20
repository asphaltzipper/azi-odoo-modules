# Copyright 2020 Matt taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Stock Forecast Detail",
    "version": "12.0.1.0.0",
    "summary": "Schedule of Future Product Stock Moves with Running Balance",
    "category": "Stock",
    "author": "Matt Taylor",
    "website": "http://www.github.com/asphaltzipper",
    "description": """
Stock Forecast Detail
=====================
For a specified product, generate a schedule of future stock moves, with
running balance.
Unless Real-Only is specified, we also include the following:
* RFQs (unconfirmed purchase orders)
* Planned orders from mrp_multi_level
* Quotations (unconfirmed sale orders)
* Submitted stock requests
    """,
    "depends": [
        "product",
        "stock",
        "purchase",
        "sale",
        "azi_mrp_multi_level",
    ],
    "data": [
        "views/stock_forecast_detail_line_views.xml",
        "views/product_views.xml",
        "views/mrp_inventory_views.xml",
        "wizards/stock_forecast_detail_views.xml",
    ],
    "installable": True,
    "auto_install": False,
}
