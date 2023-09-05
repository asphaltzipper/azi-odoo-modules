# -*- coding: utf-8 -*-
# Copyright 2016 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Sales Team Auto Assign",
    "summary": "Auto assign sales teams to customers by region and industry.",
    "version": "16.0.1.0.0",
    "category": "Sales",
    "website": "http://www.github.com/asphaltzipper/azi-odoo-modules",
    'description': "Auto assign sales teams to customers, based on criteria controlled in other modules.",
    "author": "scosist",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["crm", "sales_team_industry"],
    "data": [
        # TODO: Restrict access
        'security/ir.model.access.csv',
        'views/res_partner_view.xml',
        'wizards/sales_team_assign.xml',
    ],
    "demo": [
    ],
}
