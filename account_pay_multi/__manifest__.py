# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# commit c5c2287fb8ccafbd1efd4414f1d51105e0908593
# https://github.com/bistaray/odoo-apps.git

{
    'license': 'LGPL-3',
    'name': 'Multiple Vendor Payment',
    'version': '1.10.1',
    'category': 'Accounting',
    "author": 'Bista Solutions',
    'summary': 'Select and pay multiple Vendor Bills (Bista)',
    'description': 'For Odoo Version 10.0, this module allows users to select multiple open Vendor Invoices to pay.',
    'maintainer': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com/erp-implementation-company/erp-customization-company',
	'images': ['static/description/banner.png'],
    'depends': [
        'account',
    ],
    'init_xml': [],
    'demo_xml' :[],
    'data': [
        'views/account_payment_view.xml'
    ],
    'test': [],
    "auto_install": False,
    "application": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
