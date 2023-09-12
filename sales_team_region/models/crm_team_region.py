# Copyright 2014-2016 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class CrmTeamRegion(models.Model):
    _name = 'crm.team.region'
    _description = 'Sales Team Regions'

    name = fields.Char(
        string='Sales Region',
        required=True,
        translate=True)
    region_types = fields.Many2many(
        comodel_name='crm.team.region.type',
        column1='region_type_id',
        column2='region_id',
        string='Region Team Type(s)')
    states = fields.Many2many(
        comodel_name='res.country.state',
        relation='crm_team_region_state_rel',
        column1='region_id',
        column2='state_id')
    countries = fields.Many2many(
        comodel_name='res.country',
        relation='crm_team_region_country_rel',
        column1='region_id',
        column2='country_id')
    country_groups = fields.Many2many(
        comodel_name='res.country.group',
        relation='crm_team_region_country_group_rel',
        column1='region_id',
        column2='country_group_id')

    s_dom = fields.Many2many('res.country.state', compute='_compute_dom')
    c_dom = fields.Many2many('res.country', compute='_compute_dom')
    cg_dom = fields.Many2many('res.country.group', compute='_compute_dom')

    # onchange concerns:
    # https://github.com/odoo/odoo/issues/11295#issuecomment-242644753
    # http://stackoverflow.com/questions/36041421/odoo-custom-filter-domain-field-on-load-view
    # other potential onchange concerns:
    # http://stackoverflow.com/questions/35840533/odoo-8-api-onchange-function-not-let-update-created-one2many-value/35841753#35841753
    # http://stackoverflow.com/questions/32326212/one2many-field-on-change-function-cant-change-its-own-value
    def get_regions(self, state_ids, state_country_ids, country_ids, country_group_ids, states, countries, country_groups):
        for state in states:
            state_ids.add(state.id)
            state_country_ids.add(state.country_id.id)
        for country in countries:
            country_ids.add(country.id)
            for state in self.env['res.country.state'].search([('country_id', '=', country.id)]):
                state_ids.add(state.id)  # exclude states of countries
            for country_group in self.env['res.country'].search([('id', '=', country.id)]).country_group_ids:
                country_group_ids.add(country_group.id)
        for country_group in country_groups:
            country_group_ids.add(country_group.id)
            for country in country_group.country_ids:
                country_ids.add(country.id)  # countries of country_groups
                for state in self.env['res.country.state'].search([('country_id', '=', country.id)]):
                    state_ids.add(state.id)
        return state_ids, state_country_ids, country_ids, country_group_ids

    def region_domain(self):
        state_ids = set()
        state_country_ids = set()
        country_ids = set()
        country_group_ids = set()
        # add existing regions for domain exclusion
        # look at optimizing this in the future
        main_states, main_countries, main_groups = self.states._origin, self.countries._origin, self.country_groups._origin

        for record in self.env['crm.team.region'].search([('region_types', 'in', self.region_types.ids), ('id', '!=', self._origin.id )]):
            state_ids, state_country_ids, country_ids, country_group_ids = self.get_regions(state_ids,
                                                                                            state_country_ids,
                                                                                            country_ids,
                                                                                            country_group_ids,
                                                                                            record.states,
                                                                                            record.countries,
                                                                                            record.country_groups)
        for country_id in state_country_ids:
            country_ids.add(country_id)
            for country_group in self.env['res.country'].search([('id', '=', country_id)]).country_group_ids:
                country_group_ids.add(country_group.id)
        state_ids, state_country_ids, country_ids, country_group_ids = self.get_regions(
            state_ids, state_country_ids, country_ids, country_group_ids, main_states, main_countries, main_groups)
        return set(state_ids), set(country_ids), set(country_group_ids)

    @api.constrains('states', 'countries', 'country_groups')
    def _require_region_definition(self):
        for record in self:
            if not (record.states or record.countries or
                    record.country_groups):
                raise ValidationError(_("Sales regions require a valid region"
                                        " definition. Please select at least"
                                        " one state, country, or country"
                                        " group."))

    @api.depends('country_groups', 'countries', 'states', 'region_types')
    def _compute_dom(self):
        for record in self:
            state_ids, country_ids, country_group_ids = record.region_domain()
            record.s_dom = self.env['res.country.state'].search([('id', 'not in', list(state_ids))])
            record.c_dom = self.env['res.country'].search([('id', 'not in', list(country_ids))])
            record.cg_dom = self.env['res.country.group'].search([('id', 'not in', list(country_group_ids))])
