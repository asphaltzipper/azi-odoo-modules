# -*- coding: utf-8 -*-
# Copyright 2017 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

# https://github.com/OCA/account-financial-reporting#10.0
# commit: d473e153a6cbf00c9ebcae1730be00c193b72cc4
# 2/26/2018

{
    'name': 'Customer Outstanding Statement',
    'version': '10.0.1.0.0',
    'category': 'Accounting & Finance',
    'summary': 'OCA Financial Reports',
    'author': "Eficent, Odoo Community Association (OCA)",
    'website': 'https://github.com/OCA/account-financial-reporting',
    'license': 'AGPL-3',
    'depends': [
        'account',
    ],
    'data': [
        'views/statement.xml',
        'wizard/customer_outstanding_statement_wizard.xml',
    ],
    'installable': True,
    'application': False,
}
