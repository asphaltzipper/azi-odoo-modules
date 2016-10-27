# -*- coding: utf-8 -*-
# (c) 2016 Matt Taylor
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "MRP-1",
    "version": "1.0",
    "summary": "Material Requirements Planning One",
    "category": "Manufacturing",
    "author": "mtaylor",
    "website": "http://www.github.com/asphaltzipper/azi-odoo-modules",
    "depends": [
        "mrp",
        "procurement",
        "mrp_llc",
    ],
    "data": [
        "wizard/mrp_material_plan_compute_views.xml",
        "views/mrp_production_view.xml",
        "views/mrp_material_plan_view.xml",
    ],
    "installable": True,
    "auto_install": False,
}
