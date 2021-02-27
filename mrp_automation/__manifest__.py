# (c) 2018 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "MRP Automation",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
    "summary": "Barcode features for automating creating/completing MOs",
    "category": "Manufacturing",
    "author": "Matt Taylor",
    "website": "http://www.github.com/asphaltzipper",
    'description': """
MRP Automation
==============

* Create a Manufacturing Order by scanning a production kit barcode
* Produce a Manufacturing Order (i.e. launch and fill the produce wizard) by scanning the MO barcode
""",
    "depends": [
        "stock",
        "mrp",
        "hr",
        "mrp_wo_produce",
        "mrp_planned_pick_kit",
    ],
    "data": [
        'views/barcode_templates.xml',
        'wizard/mrp_wo_hour_views.xml',
        'views/hr_employee_views.xml',
        'wizard/mrp_automation_views.xml',
        'wizard/mrp_wo_produce_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
