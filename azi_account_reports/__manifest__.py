# -*- coding: utf-8 -*-
# (c) 2024 Matt Taylor
# see https://github.com/csnauwaert/


{
    'name': 'AZI Enterprise Accounting Reports',
    'version': '16.0.1.0.0',
    'summary': 'AZI Enterprise Custom Accounting Reports',
    'category': 'Accounting',
    'author': 'matt454357',
    "license": "AGPL-3",
    'website': 'http://www.github.com/asphaltzipper',
    'description': """
AZI Enterprise Custom Accounting Reports
========================================

* AZI Specific Financial Statements
    * Depends on a change to the chart of accounts
        * /azi-odoo-install/upgrades/upgrade_chart_of_accounts_2018-06.py
        * /azi-odoo-install/upgrades/upgrade_chart_of_accounts_2018-06.py.xlsx
    """,
    'depends': [
        'account',
        'account_reports',
    ],
    'data': [
        'data/account_tags.xml',
        'data/azi_account_reports.xml',
        'views/account_views.xml',
        'views/report_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'azi_account_reports/static/src/js/account_selection.js',
        ],
    },
    'installable': True,
    'auto_install': False,
}
