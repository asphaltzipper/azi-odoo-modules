# -*- coding: utf-8 -*-
# (c) 2016 Matt Taylor
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "MRP-Master-Schedule",
    "version": "1.0",
    "summary": "Material Requirements Planning Master Schedule",
    "category": "Manufacturing",
    "author": "mtaylor",
    "website": "http://www.github.com/asphaltzipper/azi-odoo-modules",
    "depends": [
        "mrp_mrp",
    ],
    "data": [
        "data/schedule_data.xml",
        "views/mrp_schedule_view.xml",
        "views/mrp_schedule_line_view.xml",
        "wizard/mrp_material_plan_compute_view.xml",
        'security/ir.model.access.csv',
    ],
    "installable": True,
    "auto_install": False,
}
