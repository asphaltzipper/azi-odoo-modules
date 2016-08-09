# -*- coding: utf-8 -*-
# Copyright 2014-2016 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models
from openerp.tools.translate import _


class SalesTeamRegionStateRel(models.Model):
    _name = 'sales.team.region.state.rel'

    region_id = fields.Many2one('sales.team.region', 'Sales Region',
                                required=True, translate=True,
                                ondelete='cascade')
    state_id = fields.Many2one('res.country.state', 'State', required=True,
                               translate=True)

    _sql_constraints = [
        ('rel_state_uniq', 'unique(state_id)',
         _('A region with the same state already exists [rel_state_uniq]')),
    ]
