# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP Module
#    
#    Copyright (C) 2014 Asphalt Zipper, Inc.
#    Author Matt Taylor

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
    "name": "simple_timesheet_task",
    "version": "0.1",
    "summary": "Tasks on Timesheet",
    "category": "Project Management",
    "author": "Matt Taylor",
    "website": "http://www.asphaltzipper.com",
    'description': """
Specify Tasks on Timesheet Details Tab
=========================================
    """,
    "depends": ["hr_timesheet", "hr_timesheet_sheet"],
    "data": [
        'simple_timesheet_task_view.xml',
    ],
    "installable": True,
    "auto_install": False,
}