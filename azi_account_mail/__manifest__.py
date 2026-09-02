# (c) 2025 John Welch

{
    "name": "AZI Account Mail",
    "version": "16.0.1.0.0",
    "summary": "Invoice, Mail",
    "category": "Accounting/Accounting",
    "author": "John Welch",
    "license": "AGPL-3",
    "website": "http://www.github.com/asphaltzipper",
    "description": """
        Send invoice email to partner invoice address
    """,
    "depends": [
        'azi_partner_statement',
    ],
    "data": [
        'security/ir.model.access.csv',
        'data/outstanding_mail_template.xml',
        'wizards/outstanding_statement_wizard_views.xml',
        'views/account_mail_log_views.xml',
        'views/account_move_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
