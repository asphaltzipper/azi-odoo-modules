# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

# commit 648315dadf47cf56bb0eec452d16b333ff935a2f
# Author: Pedro M. Baeza <pedro.baeza@gmail.com>
# Date:   Thu Oct 6 16:13:01 2016 +0200
# https://github.com/OCA/web/tree/10.0

{
    'name': 'Show selected sheets with full width',
    'version': '8.0.0.1.0',
    'license': 'AGPL-3',
    'author': 'Noviat, Odoo Community Association (OCA)',
    'category': 'Hidden',
    'depends': [
        'web',
    ],
    'data': [
        'views/sheet.xml',
    ],
    'active': False,
    'installable': False,
    }
