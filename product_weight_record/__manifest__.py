{
    "name": "Product Weight Record",
    "summary": "Record weight entries optionally linked to serial numbers or products",
    "version": "16.0.1.0.0",
    "category": "Inventory",
    "author": "Matt Taylor",
    "website": "https://github.com/asphaltzipper/azi-odoo-modules",
    "license": "LGPL-3",
    "depends": ["stock"],
    "data": [
        "views/product_weight_record_views.xml",
        "views/product_weight_record_accy_views.xml",
        "views/product_weight_record_method_views.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "application": False
}
