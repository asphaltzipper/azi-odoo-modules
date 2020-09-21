# -*- coding: utf-8 -*-
{
    "name": "AZI Partner Statement",
    "version": "12.0.1.0.0",
    "summary": "Partner Statement",
    "category": "Accounting",
    "author": "John Welch",
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
        'reports/outstanding_statement.xml',
        'reports/activity_statement.xml',
    ],
    "installable": True,
    "auto_install": False,
}
