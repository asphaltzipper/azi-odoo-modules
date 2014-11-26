# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP Module
#
#    Copyright (C) 2014 Asphalt Zipper, Inc.
#    Author Scott Saunders
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'AZI Accountng Enhancements',
    'version': '0.1',
    'summary': 'AZI Accounting Enhancements',
    'category': 'Accounting & Finance',
    'author': 'matt454357',
    'website': 'http://asphaltzipper.com',
    'description': """
Accounting enhancements for AZI
================================
- Add active field to account type
- Show accounts list of account type view
- Import account payment terms
    """,
    'depends': ['account'],
    'data': [
        'account_view.xml',
    ],
    'demo': [],
    'test': [],
    'js': [],
    'css': [],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
