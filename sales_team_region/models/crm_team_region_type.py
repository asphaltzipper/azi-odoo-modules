# -*- coding: utf-8 -*-
# Copyright 2016-2017 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CrmTeamRegionType(models.Model):
    _name = 'crm.team.region.type'
    _description = 'Sales Team Region Type'

    name = fields.Char('Region Team Type', required=True, translate=True)
    color = fields.Integer('Color Index')
