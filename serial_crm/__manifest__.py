# (c) 2017 Matt Taylor

{
    "name": "Serial CRM",
    "version": "12.0.1.0.0",
    "summary": "Extra Info for Serialized Products",
    "category": "Inventory",
    "author": "Chris Emigh",
    "website": "http://www.github.com/asphaltzipper",
    'description': """
        Add fields for additional info and for linking serials with customers
    """,
    "depends": [
        "repair",
        "stock_inventory_revaluation",
        "attachment_priority",
        "mrp_plm",
    ],
    "data": [
        'security/ir.model.access.csv',
        'report/combined_bom_report.xml',
        'views/bom_template.xml',
        'views/stock_lot_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'report/combined_bom_template.xml',
        'report/lot_serial_report.xml',
        'report/serial_crm_reports.xml',
        'data/serial_crm_data.xml',
    ],
    "installable": True,
    "auto_install": False,
}
