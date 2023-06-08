# Author: Scott Saunders. Copyright Asphalt Zipper, Inc.
# Contributors: Matt Taylor
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Purchase Line Delivery",
    "version": "1.0",
    "summary": "Purchase Order Line delivery method",
    "category": "Purchases",
    "author": "Scott Saunders",
    'license': 'AGPL-3',
    "website": "http://www.github.com/asphaltzipper/azi-odoo-modules",
    'description': """
        Add a field on purchase order line for specifying a delivery method.
    """,
    "depends": ["purchase_stock", "delivery"],
    "data": [
        'views/purchase_views.xml',
        'views/res_config_settings_views.xml',
        'report/templates.xml',
    ],
    "installable": True,
    "auto_install": False,
}
