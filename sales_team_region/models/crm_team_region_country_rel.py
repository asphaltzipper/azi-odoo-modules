# -*- coding: utf-8 -*-
# Copyright 2014-2016 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CrmTeamRegionCountryRel(models.Model):
    _name = 'crm.team.region.country.rel'

    region_id = fields.Many2one('crm.team.region', 'Sales Region',
                                required=True, ondelete='cascade')
    country_id = fields.Many2one('res.country', 'Country', required=True)
