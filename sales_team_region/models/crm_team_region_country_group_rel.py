# -*- coding: utf-8 -*-
# Copyright 2014-2016 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models
#from openerp.tools.translate import _


class CrmTeamRegionCountryGroupRel(models.Model):
    _name = 'crm.team.region.country.group.rel'

    region_id = fields.Many2one('crm.team.region', 'Sales Region',
                                required=True, ondelete='cascade')
    country_group_id = fields.Many2one('res.country.group', 'Country Group',
                                       required=True)

    #_sql_constraints = [
    #    ('rel_country_group_uniq', 'unique(country_group_id)',
    #     _('A region with the same country group already exists'
    #       ' [rel_country_group_uniq]')),
    #]
