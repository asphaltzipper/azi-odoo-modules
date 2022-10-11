# Copyright 2017 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "azi_mrp",
    "version": "12.0.1.0.0",
    "summary": "AZI MRP Customizations",
    "category": "Manufacturing",
    "author": "Matt Taylor",
    "license": "AGPL-3",
    "website": "http://www.asphaltzipper.com",
    'description': """
AZI Specialized Customizations to MRP
=====================================

* Show stock moves button on MO form
* Add serial-required column to raw material list for sorting
* Change repair order account move names to the name of the repair order
* Replace product Manufactured button
* Wizard to compile PDF files
    """,
    "depends": [
        'stock',
        'mrp',
        'shelf_location',
        'attachment_priority',
        'electronic_kanban',
        'base_report_to_printer',
        'engineering_product',
    ],
    'data': [
        'views/report_bom_template.xml',
        'views/mrp_view_changes.xml',
        'views/mrp_bom_views.xml',
        'views/mrp_bom_history_views.xml',
        'report/mrp_bom_history_report.xml',
        'report/mrp_report.xml',
        'report/mrp_production_templates.xml',
        'report/product_report_bom_structure.xml',
        'report/mrp_report_bom_structure.xml',
        'views/production_move_analysis.xml',
        'views/product_views.xml',
        'wizards/compile_product_file_views.xml',
        'security/ir.model.access.csv',
    ],
    "installable": True,
    "auto_install": False,
}
