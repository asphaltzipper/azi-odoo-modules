# -*- coding: utf-8 -*-
# Copyright 2014-2016 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import ValidationError
from openerp.tools.translate import _


class SalesTeamRegion(models.Model):
    _name = 'sales.team.region'

    name = fields.Char('Sales Region', required=True, translate=True)
    states = fields.Many2many('res.country.state',
                              'sales_team_region_state_rel', 'region_id',
                              'state_id', domain=lambda self: [
                                  ('id', 'not in', self._region_domain(1))])
    countries = fields.Many2many('res.country',
                                 'sales_team_region_country_rel', 'region_id',
                                 'country_id', domain=lambda self: [
                                     ('id', 'not in', self._region_domain(2))])
    country_groups = fields.Many2many('res.country.group',
                                      'sales_team_region_country_group_rel',
                                      'region_id', 'country_group_id',
                                      domain=lambda self: [
                                          ('id', 'not in',
                                           self._region_domain(3))])

    @api.model
    @api.constrains('states', 'countries', 'country_groups')
    def _require_region_definition(self):
        for record in self:
            if not (record.states or record.countries or
                    record.country_groups):
                raise ValidationError(_("Sales regions require a valid region"
                                        " definition. Please select at least"
                                        " one state, country, or country"
                                        " group."))

                # exclude state country_ids
    @api.multi
    def _region_domain(self, region=False):
        state_ids = set()
        state_country_ids = set()
        country_ids = set()
        country_group_ids = set()
        # add existing regions for domain exclusion
        # look at optimizing this in the future
        for record in self.env['sales.team.region'].search([]):
            for state in record.states:
                state_ids.add(state.id)
                # exclude state country_ids
                state_country_ids.add(state.country_id.id)
                #for country_group in self.env['res.country'].search([('id','=',state.country_id.id)]).country_group_ids:
                #    country_group_ids.add(country_group.id)
            for country in record.countries:
                country_ids.add(country.id)
                for state in self.env['res.country.state'].search(
                        [('country_id', '=', country.id)]):
                    state_ids.add(state.id)  # exclude states of countries
                for country_group in self.env['res.country'].search(
                        [('id', '=', country.id)]).country_group_ids:
                    country_group_ids.add(country_group.id)
            for country_group in record.country_groups:
                country_group_ids.add(country_group.id)
                for country in country_group.country_ids:
                    country_ids.add(country.id)  # countries of country_groups
                    for state in self.env['res.country.state'].search(
                            [('country_id', '=', country.id)]):
                        state_ids.add(state.id)  # states of countries of etc.
        for country_id in state_country_ids:
            country_ids.add(country_id)
            for country_group in self.env['res.country'].search(
                    [('id', '=', country_id)]).country_group_ids:
                country_group_ids.add(country_group.id)
        region_domain = {1: list(state_ids), 2: list(country_ids),
                         3: list(country_group_ids)}
        if region:
            return region_domain.get(region, list())
        else:
            return set(state_ids), set(country_ids), set(country_group_ids)

    @api.onchange('country_groups', 'countries', 'states')
    def onchange_region(self):
        state_ids, country_ids, country_group_ids = self._region_domain()
        state_country_ids = set()
        # add currently selected regions for domain exclusion
        for state in self.states:
            for state_id in self.env['res.country.state'].browse(state.id):
                state_country_ids.add(state_id.country_id.id)
                #for country_group in self.env['res.country.group'].search([('country_ids','in',state_id.country_id.id)]):
                #    country_group_ids.add(country_group.id)
        for country_id in state_country_ids:
            country_ids.add(country_id)
            for country_group in self.env['res.country'].search(
                    [('id', '=', country_id)]).country_group_ids:
                country_group_ids.add(country_group.id)
        for country in self.countries:
            for state in self.env['res.country.state'].search(
                    [('country_id', '=', country.id)]):
                state_ids.add(state.id)
            for country_group in self.env['res.country.group'].search(
                    [('country_ids', 'in', country.id)]):
                country_group_ids.add(country_group.id)
        for country_group in self.country_groups:
            for country in self.env['res.country.group'].browse(
                    country_group.id)['country_ids']:
                country_ids.add(country.id)
                for state in self.env['res.country.state'].search(
                        [('country_id', '=', country.id)]):
                    state_ids.add(state.id)
        return {'domain': {'states': [('id', 'not in', list(state_ids))],
                           'countries': [('id', 'not in', list(country_ids))],
                           'country_groups': [('id', 'not in',
                                               list(country_group_ids))]}}
