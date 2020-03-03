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
    'depends': ['product', 'stock', 'mrp', 'barcodes', 'azi_stock'],
    'data': [
        'views/stock_shelf_views.xml',
        'views/product_views.xml',
        # 'views/shelf_location_barcode_template.xml',
        'security/ir.model.access.csv',
        'report/product_labels.xml',
        'report/product_report.xml',
        'report/shelf_product_listing_templates.xml',
        'report/shelf_report.xml',
        'report/transfer_slip_template.xml',

    ],
    'installable': True,
    'auto_install': False,
}
