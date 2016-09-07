# -*- coding: utf-8 -*-
# Copyright 2014-2016 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import ValidationError
from openerp.tools.translate import _


class CrmTeamRegion(models.Model):
    _name = 'crm.team.region'

    name = fields.Char('Sales Region', required=True, translate=True)
    # region_type_id = fields.Many2one('crm.team.region.type', 'Region Type')
    region_types = fields.Many2many('crm.team.region.type',
                                    column1='region_type_id',
                                    column2='region_id',
                                    string='Region Team Type(s)')
    states = fields.Many2many('res.country.state',
                              'crm_team_region_state_rel', 'region_id',
                              'state_id')
    #                          'state_id', domain=lambda self: [
    #                              ('id', 'not in', self._region_domain(1))])
    countries = fields.Many2many('res.country',
                                 'crm_team_region_country_rel', 'region_id',
                                 'country_id')
    #                             'country_id', domain=lambda self: [
    #                                 ('id', 'not in', self._region_domain(2))])
    country_groups = fields.Many2many('res.country.group',
                                      'crm_team_region_country_group_rel',
                                      'region_id', 'country_group_id')
    #                                  'region_id', 'country_group_id',
    #                                  domain=lambda self: [
    #                                      ('id', 'not in',
    #                                       self._region_domain(3))])

    # domain fields parameter appears to no longer be supported

    # https://www.odoo.com/fr_FR/forum/aide-1/question/conditionally-apply-domain-on-a-field-25468
    # https://www.odoo.com/fr_FR/forum/aide-1/question/filter-column-with-domain-and-funtion-72329
    # using fields_view_get is too early in the load process, we don't have the
    #  form view region object yet
    #@api.model
    #def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #    res = super(CrmTeamRegion, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=submenu)
    #    if view_type != 'form':
    #        return res
    #    from lxml import etree
    #    doc = etree.XML(res['arch'])
    #    for node in doc.xpath("//field[@name='states']"):
    #        domain = "[('id', 'not in'," + str(self._region_domain(1)) + ")]"
    #        node.set('domain', domain)
    #        res['arch'] = etree.tostring(doc)
    #    return res

    # https://www.odoo.com/fr_FR/forum/aide-1/question/filter-column-with-domain-and-funtion-72329
    # http://stackoverflow.com/questions/30341476/is-there-any-way-to-call-a-function-when-a-record-is-requested-to-be-shown-in-a
    # unfinished attempts at default_get and read for sub-region domain
    #  filtering on create and read
    # should perhaps consider trying set_value
    #@api.model
    #def default_get(self, fields):
    #    res = super(CrmTeamRegion, self).default_get(fields)
    #    domain = "[('id', 'not in'," + str(self._region_domain(1)) + ")]"
    #    res = {'domain': {'states': domain }}
    #    return res

    # broken: never enters the if and seems to be resetting the domain
    #@api.multi
    #def read(self, fields=None, load='_classic_read'):
    #    res = super(CrmTeamRegion, self).read(fields, load=load)
    #    if 'states' in fields and '__last_update' in fields:
    #        domain = "[('id', 'not in',self._region_domain(1))]"
    #       #res['domain']['states'] = domain
    #        self.states.domain = domain
    #    return res

    # https://www.odoo.com/fr_FR/forum/aide-1/question/conditionally-apply-domain-on-a-field-25468
    # https://www.odoo.com/fr_FR/groups/community-59/community-13935621?mode=thread&date_begin=&date_end=
    # https://www.odoo.com/fr_FR/forum/aide-1/question/on-change-alternative-for-dynamic-domain-on-form-edit-15912
    # https://www.odoo.com/fr_FR/forum/aide-1/question/filter-column-with-domain-and-funtion-72329
    # http://stackoverflow.com/questions/30341476/is-there-any-way-to-call-a-function-when-a-record-is-requested-to-be-shown-in-a
    # http://stackoverflow.com/questions/31825713/odoo-filter-many2one-field-on-load
    # https://www.odoo.com/fr_FR/forum/aide-1/question/how-to-apply-domain-filter-on-many2many-field-28988
    # workaround to filter sub-region lists on form view load as follows
    # note: domain fields parameter must not be defined for this to work
    @api.multi
    #@api.depends('country_groups', 'countries', 'states', 'region_types')
    def _compute_dom(self):
        self.s_dom = self._region_domain(1)
        self.c_dom = self._region_domain(2)
        self.cg_dom = self._region_domain(3)

    # https://gist.github.com/dreispt/a4c30fe671db2b2fce34
    s_dom = fields.Many2many('res.country.state', compute=_compute_dom)
    c_dom = fields.Many2many('res.country', compute=_compute_dom)
    cg_dom = fields.Many2many('res.country.group', compute=_compute_dom)

    # onchange concerns:
    # https://github.com/odoo/odoo/issues/11295#issuecomment-242644753
    # http://stackoverflow.com/questions/36041421/odoo-custom-filter-domain-field-on-load-view
    # other potential onchange concerns:
    # http://stackoverflow.com/questions/35840533/odoo-8-api-onchange-function-not-let-update-created-one2many-value/35841753#35841753
    # http://stackoverflow.com/questions/32326212/one2many-field-on-change-function-cant-change-its-own-value

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
    @api.depends('region_types')
    def _region_domain(self, geoslice=False):
        #if geoslice:
        #    return list()
        #else:
        #    return set(), set(), set()
        state_ids = set()
        state_country_ids = set()
        country_ids = set()
        country_group_ids = set()
        #import pdb
        #pdb.set_trace()
        # add existing regions for domain exclusion
        # look at optimizing this in the future
        for record in self.env['crm.team.region'].search(
                [('region_types', 'in', self.region_types.ids)]):
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
        if geoslice:
            return region_domain.get(geoslice, list())
        else:
            return set(state_ids), set(country_ids), set(country_group_ids)

    @api.onchange('country_groups', 'countries', 'states', 'region_types')
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
