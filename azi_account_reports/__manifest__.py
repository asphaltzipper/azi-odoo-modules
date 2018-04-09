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

* Report Profit and Loss, grouped by product/category details
    """,
    'depends': [
        'account',
        'account_reports',
    ],
    'data': [
        'data/account_tags.xml',
        'data/azi_account_reports.xml',
        'views/account_views.xml',
        # 'views/turnover_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
