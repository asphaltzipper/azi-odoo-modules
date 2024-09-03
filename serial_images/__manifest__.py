# (c) 2024 Matt Taylor
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Serial Images",
    "version": "16.0.1.0.0",
    "summary": "Image Books for Serialized Product Builds",
    "category": "Inventory",
    "author": "Matt Taylor",
    "website": "http://www.github.com/asphaltzipper",
    'description': """
        Upload images and make notes on serial numbered builds
    """,
    "depends": [
        "stock",
        "attachment_priority",
        "serial_crm",
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/stock_lot_views.xml',
        'views/serial_images_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
