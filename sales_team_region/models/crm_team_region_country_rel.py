# -*- coding: utf-8 -*-
# Copyright 2014-2016 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models
#from openerp.tools.translate import _


class CrmTeamRegionCountryRel(models.Model):
    _name = 'crm.team.region.country.rel'

    region_id = fields.Many2one('crm.team.region', 'Sales Region',
                                required=True, ondelete='cascade')
    country_id = fields.Many2one('res.country', 'Country', required=True)

    #_sql_constraints = [
    #    ('rel_country_uniq', 'unique(country_id)',
    #     _('A region with the same country already exists'
    #       ' [rel_country_uniq]')),
    #]
