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
    ],
    'data': [
        'views/stock_shelf_views.xml',
        'views/product_views.xml',
        'security/ir.model.access.csv',
        'report/shelf_product_listing_templates.xml',
        'report/shelf_report.xml',
    ],
    'demo': [
        'data/shelf_location_demo.xml',
    ],
    'installable': True,
    'auto_install': False,
}
