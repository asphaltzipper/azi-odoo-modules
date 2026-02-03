# (c) 2025 John Welch

{
    "name": "Portal Serials",
    "version": "16.0.1.0.0",
    "summary": "Show Owned Serials in the Customer Portal",
    "category": "Sales/CRM",
    "author": "John Welch",
    "license": "AGPL-3",
    "website": "http://www.github.com/asphaltzipper",
    'description': """
        Display serial numbers and other details for portal users
    """,
    "depends": [
        "serial_crm",
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/sale_views.xml',
        'views/account_move_views.xml',
        'views/breadcrumbs_templates.xml',
        'views/serial_portal_templates.xml',
        'views/sale_portal_templates.xml',
    ],
    "assets": {
        'web.assets_frontend': [
            'portal_serials/static/src/js/customer_portal.js',
        ],
    },
    "installable": True,
    "auto_install": False,
}
