# -*- coding: utf-8 -*-
# Copyright 2014-2016 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class CrmTeamRegionStateRel(models.Model):
    _name = 'crm.team.region.state.rel'

    region_id = fields.Many2one('crm.team.region', 'Sales Region',
                                required=True, ondelete='cascade')
    state_id = fields.Many2one('res.country.state', 'State', required=True)
