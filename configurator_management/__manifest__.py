# -*- coding: utf-8 -*-
# (c) 2016 Matt Taylor
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Configurator Management",
    "version": "1.0",
    "description": "Tools for managing configurator data",
    "summary": "Tools for managing configurator data",
    "category": "Manufacturing",
    "author": "mtaylor",
    "website": "http://www.github.com/asphaltzipper/azi-odoo-modules",
    "depends": [
        "mrp",
        "product_configurator",
        "product_configurator_mrp",
    ],
    "data": [
        "views/product_views.xml",
    ],
    "installable": True,
    "auto_install": False,
}
