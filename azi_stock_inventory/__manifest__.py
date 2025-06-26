# (c) 2025 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "AZI Stock Inventory Adjustment",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "summary": "Add features to OCAs Stock Inventory Adjustment module for AZI",
    "category": "Inventory/Inventory",
    "author": "Matt Taylor",
    "website": "http://www.github.com/asphaltzipper",
    'description': """
AZI Stock Inventory Adjustment
==============================

* Require products before beginning manual adjustments
""",
    "depends": ["stock_inventory"],
    'assets': {
        'web.assets_backend': [
            'azi_stock_inventory/static/src/js/inventory_report_list_controller.js',
            ('replace', 'stock/static/src/views/list/inventory_report_list_view.js',
             'azi_stock_inventory/static/src/js/inventory_report_list_view.js'),
        ],

    },
    "data": [],
    "installable": True,
    "auto_install": False,
}
