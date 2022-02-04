# (c) 2016 Matt Taylor
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Configurator Management",
    "version": "12.0.1.0.0",
    "description": "Tools for managing configurator data",
    "license": "AGPL-3",
    "summary": "Tools for managing configurator data",
    "category": "Manufacturing",
    "author": "mtaylor",
    "website": "http://www.github.com/asphaltzipper/azi-odoo-modules",
    "depends": [
        "mrp",
        "product",
        "product_configurator",
        "product_configurator_mrp",
    ],
    "data": [
        "views/product_views.xml",
        "views/mrp_bom_views.xml",
        "views/product_attribute_views.xml",
        'security/ir.model.access.csv',
    ],
    "installable": True,
    "auto_install": False,
}
