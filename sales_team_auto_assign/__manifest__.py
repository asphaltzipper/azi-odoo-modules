# -*- coding: utf-8 -*-
# Copyright 2016 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Sales Team Auto Assign",
    "summary": "Auto assign sales teams to customers by region and industry.",
    "version": "10.0.1.0.0",
    "category": "Sales",
    "website": "http://www.github.com/asphaltzipper/azi-odoo-modules",
    "author": "scosist",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["crm", "sales_team_industry"],
    "data": [
        'security/ir.model.access.csv',
        'views/res_partner_view.xml',
    ],
    "demo": [
    ],
}
