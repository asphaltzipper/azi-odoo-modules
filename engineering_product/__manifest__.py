# Copyright (C) 2017 Asphalt Zipper, Inc.
# Author Matt Taylor

{
    "name": "engineering_product",
    "version": "12.0.1.0.0",
    "summary": "Engineering Features for Products",
    "category": "Engineering",
    "author": "Matt Taylor",
    "license": "AGPL-3",
    "website": "http://www.asphaltzipper.com",
    'description': """
Engineering Features for Products
=================================

* Require Unique Product Code (product.default_code)
* Create eng code sequence
* Create engineering categories
* Add engineering code and revision fields
* Constrain eng code format (using regular expression)
* Add Deprecated field
    """,
    "depends": [
        'product',
        'stock',
        'shelf_location',
        'attachment_priority',
    ],
    'data': [
        'data/product_data.xml',
        'views/product_views.xml',
        'views/shelf_location_views.xml',
        'views/engineering_category_views.xml',
        'views/engineering_attribute_views.xml',
        'security/ir.model.access.csv',
        'data/engineering.part.type.csv',
    ],
    "installable": True,
    "auto_install": False,
}
