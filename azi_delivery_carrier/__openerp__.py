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
    'name' : 'AZI Delivery Methods',
    'version' : '0.1',
    'summary': 'Import delivery carriers for AZI',
    'category' : 'Technical Settings',
    'author' : 'scosist',
    'website': 'http://asphaltzipper.com',
    'description' : 'Import Delivery Methods for AZI into delivery.carrier',
    'depends' : ['base', 'product', 'delivery'],
    'data' : [
        'carrier_data.xml',
    ],
    'demo': [],
    'test': [],
    'js': [],
    'css': [],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
