{
    'name': 'Shelf Location',
    'category': 'stock',
    'summary': 'Shelf Location',
    'version': '12.0.1.0.0',
    'description': """
Shelf Location
=================

* Create shelf locations
* Create field fo shelf location
* Create barcode scanning for barcodes

        """,
    'author': "Chris Emigh",
    'license': 'AGPL-3',
    'depends': [
        'product',
        'stock',
        'mrp',
        'barcodes',
        'web_notify',
    ],
    'data': [
        'wizard/wizard_shelf_product_scan_views.xml',
        'views/stock_shelf_views.xml',
        'views/product_views.xml',
        'report/shelf_product_listing_templates.xml',
        'report/shelf_label_templates.xml',
        'report/shelf_count_sheets_templates.xml',
        'report/shelf_report.xml',
        'report/report_stock_shelf_products_views.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        'data/shelf_location_demo.xml',
    ],
    'installable': True,
    'auto_install': False,
}
