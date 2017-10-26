# -*- coding: utf-8 -*-
# Copyright 2017 Ursa Information Systems <http://www.ursainfosystems.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# https://github.com/OCA/account-invoice-reporting.git
# commit 054fde0950f45af8b68f9c24c483dad8451df02c
# Author: OCA Transbot <transbot@odoo-community.org>
# Date:   Sat Aug 5 01:06:20 2017 +0200
#
#     OCA Transbot updated translations from Transifex

{
    'name': 'Partner Days to Pay',
    'summary': 'Adds receivables and payables statistics to partners',
    'version': '10.0.1.0.1',
    'license': 'AGPL-3',
    'author': 'Ursa Information Systems, Odoo Community Association (OCA)',
    'category': 'Accounting & Finance',
    'website': 'http://www.ursainfosystems.com',
    'depends': ['account'],
    'data': [
        'views/res_partner.xml',
    ],
    'installable': True,
}
