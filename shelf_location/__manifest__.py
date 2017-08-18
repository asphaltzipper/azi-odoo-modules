{
    'name': 'Shelf Location',
    'category': 'stock',
    'summary': 'Shelf Location',
    'version': '10.0.1.0',
    'description': """
Shelf Location
        """,
    'author': "Chris Emigh",
    'license': 'AGPL-3',
    'depends': ['product', 'stock', 'mrp'],
    'data': [
        'views/stock_shelf_views.xml',
        'views/product_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
}
