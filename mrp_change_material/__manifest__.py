# Copyright 2017 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "mrp_change_material",
    "version": "12.0.1.0.0",
    "summary": "MRP Change Material",
    "category": "Manufacturing",
    "author": "Matt Taylor",
    "website": "https://github.com/asphaltzipper",
    'description': """
Change Manufacturing Order Consumed Material
============================================

* Add a cancel button to each Consumed Materials line
* Enable creation of new Consumed Materials lines
    * Mark new lines with a new field on stock move
* Increase quantity by creating new lines
* Decrease quantity by creating a new line and canceling the old line
    """,
    "depends": ['mrp'],
    'data': [
        'wizards/add_raw_move.xml',
        'views/mrp_production_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
