# -*- coding: utf-8 -*-
{
    "name": "AZI Partner Statement",
    "version": "16.0.1.0.0",
    "summary": "Partner Statement",
    "category": "Accounting",
    "author": "John Welch",
    "license": "AGPL-3",
    "website": "http://www.github.com/asphaltzipper",
    'description': """
AZI Partner Statement
=====================
* Modified outstanding and activity reports to align address
    """,
    'depends': [
        'partner_statement',
    ],
    "data": [
        'security/ir.model.access.csv',
        'reports/outstanding_statement.xml',
        'reports/activity_statement.xml',
        'wizards/partner_due_report_views.xml',
    ],
    "installable": True,
    "auto_install": False,
}
