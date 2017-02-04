# -*- coding: utf-8 -*-
# Copyright 2014-2016 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CrmTeamRegionCountryGroupRel(models.Model):
    _name = 'crm.team.region.country.group.rel'

    region_id = fields.Many2one('crm.team.region', 'Sales Region',
                                required=True, ondelete='cascade')
    country_group_id = fields.Many2one('res.country.group', 'Country Group',
                                       required=True)
