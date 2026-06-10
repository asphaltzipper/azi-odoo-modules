# (c) 2017 Matt Taylor

{
    "name": "Sale Warranty",
    "version": "16.0.1.0.0",
    "summary": "Sale Warranty",
    "category": "Sale",
    "author": "Matt Taylor",
    "license": "AGPL-3",
    "website": "http://www.github.com/asphaltzipper",
    'description': """
        Track warranty by customer and product/serial number
    """,
    "depends": [
        "azi_stock",
        "sale",
        "sale_product_configurator",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_warranty_views.xml",
        "views/product_template_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "auto_install": False,
}
