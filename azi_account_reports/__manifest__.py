# -*- coding: utf-8 -*-
# (c) 2017 Matt Taylor
# see https://github.com/csnauwaert/


{
    'name': 'AZI Enterprise Accounting Reports',
    'version': '10.0.0.0.0',
    'summary': 'AZI Enterprise Custom Accounting Reports',
    'category': 'Accounting',
    'author': 'matt454357',
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
        'data/account.account.type.csv',
        'data/account_tags.xml',
        'data/azi_account_reports.xml',
        'views/account_views.xml',
        'views/report_views.xml',
        'views/report_financial.xml',
    ],
    'installable': True,
    'auto_install': False,
    # 'pre_init_hook': '_set_update',
    'post_init_hook': '_set_noupdate',
}
