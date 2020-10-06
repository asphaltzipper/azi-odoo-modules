# (c) 2018 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Work Order Produce Wizard",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
    "summary": "Wizard for producing/completing Manufacturing Orders with Work Orders",
    "category": "Inventory",
    "author": "Matt Taylor",
    "website": "http://www.github.com/asphaltzipper",
    'description': """
Work Order Produce Wizard
=========================
Wizard for completing Manufacturing Orders with Work Orders

Steps for processing manufacturing order:

#. Create Manufacturing Order (with a routing)
#. Check Availability
#. Plan
#. Start WO Completion Wizard
#. Enter produced serial number
#. Enter consumed serial numbers
#. Enter labor time per work order
#. Click Done to complete all work orders and the manufacturing order
""",
    "depends": [
        "stock",
        "mrp",
        "hr",
    ],
    "data": [
        'views/barcode_templates.xml',
        'wizard/mrp_wo_hour_views.xml',
        'wizard/mrp_wo_produce_views.xml',
        'views/mrp_production_views.xml',
        'views/hr_employee_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
