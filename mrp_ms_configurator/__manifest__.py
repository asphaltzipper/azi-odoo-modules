# -*- coding: utf-8 -*-
# (c) 2016 Matt Taylor
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "MRP MS Configurator",
    "version": "1.0",
    "description": "MRP MS Configurator",
    "summary": "MRP Master Schedule Configurator Wizard",
    "category": "Manufacturing",
    "author": "mtaylor",
    "website": "http://www.github.com/asphaltzipper/azi-odoo-modules",
    "depends": [
        "mrp",
        "product_configurator_wizard",
    ],
    "data": [
        "wizard/product_configurator_view.xml",
        "views/mrp_schedule_line_view.xml",
    ],
    "installable": True,
    "auto_install": False,
}
