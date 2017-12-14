# -*- coding: utf-8 -*-
# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# commit: 5cb0d4974f35423c39026d4464474887bec1a024
# Author: Houzéfa Abbasbhay <houzefa.abba@xcg-consulting.fr>
# Date:   Fri Aug 4 10:56:59 2017 +0200
# https://github.com/OCA/web/tree/10.0

{
    'name': 'Web Notify',
    'summary': """
        Send notification messages to user""",
    'version': '10.0.1.0.0',
    'description': 'Web Notify',
    'license': 'AGPL-3',
    'author': 'ACSONE SA/NV,Odoo Community Association (OCA)',
    'website': 'https://acsone.eu/',
    'depends': [
        'web',
        'bus',
    ],
    'data': [
        'views/web_notify.xml'
    ],
    'demo': [
    ],
    'installable': True,
}
