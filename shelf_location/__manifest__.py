{
    'name': 'Shelf Location',
    'category': 'stock',
    'summary': 'Shelf Location',
    'version': '10.0.1.0',
    'description': """
Shelf Location
=================

* Create shelf locations
* Create field fo shelf location
* Create barcode scanning for barcodes

        """,
    'author': "Chris Emigh",
    'license': 'AGPL-3',
    'depends': ['product', 'stock', 'mrp', 'barcodes'],
    'data': [
        'views/stock_shelf_views.xml',
        'views/product_views.xml',
        'views/shelf_location_barcode_template.xml',
        'security/ir.model.access.csv',
        'report/report_layout.xml',
        'report/mrp_production_templates.xml',
    ],
    'installable': True,
    'auto_install': False,
}
