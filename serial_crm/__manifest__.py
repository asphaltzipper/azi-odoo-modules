# (c) 2017 Matt Taylor

{
    "name": "Serial CRM",
    "version": "16.0.1.0.0",
    "summary": "Extra Info for Serialized Products",
    "category": "Inventory",
    "author": "Chris Emigh",
    "license": "AGPL-3",
    "website": "http://www.github.com/asphaltzipper",
    'description': """
        Add fields for additional info and for linking serials with customers
    """,
    "depends": [
        "repair",
        "stock_valuation_fifo_lot",
        "stock_valuation_specific_identification",
        "attachment_priority",
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/stock_lot_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'report/lot_serial_report.xml',
        'report/serial_crm_reports.xml',
        'data/serial_crm_data.xml',
    ],
    "assets": {
        'web.assets_backend': [
            'serial_crm/static/src/js/combined_bom_report.js',
        ],
    },
    "installable": True,
    "auto_install": False,
}
