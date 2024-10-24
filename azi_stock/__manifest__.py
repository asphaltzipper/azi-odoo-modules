# Copyright 2024 Chris Emigh
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "azi_stock",
    "version": "16.0.1.0.0",
    "summary": "AZI Stock Customizations",
    "category": "Warehouse",
    "author": "Chris Emigh",
    "license": "AGPL-3",
    "website": "http://www.asphaltzipper.com",
    'description': """
AZI Specialized Customizations to Stock
=======================================

* Add description to picking move lines
* Show creation date on stock picking tree
* Prevent negative quants for serial tracked products
    """,
    "depends": [
        'stock_inventory',
        'purchase',
        'engineering_product',
        'shelf_location',
        'barcode_font',
        'stock_valuation_fifo_lot',
        'stock_valuation_specific_identification',
        'serial_crm',
        # 'stock_picking_filter_lot',  # TODO: from https://github.com/OCA/stock-logistics-workflow
        # 'stock_lot_production_date',  # TODO: from https://github.com/OCA/stock-logistics-workflow
        # 'stock_production_lot_quantity_tree',  # TODO: from https://github.com/OCA/stock-logistics-warehouse
        # 'product_lot_sequence',  # TODO: modify and use from https://github.com/OCA/product-attribute
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_view_changes.xml',
        'report/transfer_slip_template.xml',
        'report/transfer_slip.xml',
        'report/product_labels.xml',
        'report/product_report.xml',
        'report/stock_quant_views.xml',
        'report/picking_report.xml',
        # 'report/location_labels.xml',
        # 'report/location_report.xml',
        'report/transfer_slip_template.xml',
        'report/stock_quant_report.xml',
        'report/stock_report.xml',
        'report/monthly_inventory_views.xml',
        'report/report_serial_plc_label.xml',
        'report/report_azi_lot_label.xml',
        'views/stock_quant_views.xml',
        'views/stock_inventory_views.xml',
        'wizards/inventory_import_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
