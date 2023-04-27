# Copyright (C) 2014 Asphalt Zipper, Inc.
# Author Matt Taylor

{
    "name": "azi_product",
    "version": "1.0",
    "summary": "AZI Product Customizations",
    "category": "Inventory Control",
    "author": "Matt Taylor",
    "license": "AGPL-3",
    "website": "http://www.asphaltzipper.com",
    'description': """
AZI Customizations to Product
=============================

* Add Product Manager field
* Require Unique UOM Category Name
* Require Unique UOM Name
    """,
    "depends": [
        'stock',
        'purchase',
    ],
    'data': [
        'views/product_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
