# (c) 2018 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Work Order Produce",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "summary": "MRP, Labor",
    "category": "Manufacturing",
    "author": "Matt Taylor",
    "website": "http://www.github.com/asphaltzipper",
    'description': """
Work Order Produce
==================

Add labor information in MO:

#. Create Manufacturing Order
#. Confirm MO, which generates labor information
#. Set employee and hours
#. Mark MO as done, which will add labor information in WO timeline
""",
    "depends": [
        "stock_account",
        "mrp",
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/mrp_production_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
