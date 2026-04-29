# (c) 2017 Matt Taylor

{
    "name": "Technical Service Bulletin",
    "version": "16.0.1.0.0",
    "summary": "Technical Service Bulletin Management for Serialized Units",
    "category": "Inventory",
    "author": "Matt Taylor",
    "license": "AGPL-3",
    "website": "http://www.github.com/asphaltzipper",
    'description': """
        Define Technical Service Bulletins (TSBs) and associate them with serialized units
    """,
    "depends": [
        "stock",
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/tsb_views.xml',
        'views/stock_lot_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
