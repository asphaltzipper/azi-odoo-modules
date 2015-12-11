# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP Module
#
#    Copyright (C) 2014 Asphalt Zipper, Inc.
#    Author scosist
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from openerp import models, fields, api
from openerp.exceptions import ValidationError
from openerp.tools.translate import _


class crm_team(models.Model):
    _inherit = 'crm.team'

    region_id = fields.Many2one('sales.team.region', 'Sales Region',
                                translate=True)


class res_partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _lookup_team(self, state_id=False, customer=False, country_id=False):
        if (state_id or country_id) and customer:
            s_region_id = False
            c_region_id = False
            cg_region_id = False
            if not country_id:
                country_id = self.env['res.country.state'].browse(
                    state_id)['country_id']['id']
            c_region_id = self.env['sales.team.region'].search(
                [('countries', 'in', country_id)])['id']
            if state_id:
                s_region_id = self.env['sales.team.region'].search(
                    [('states', 'in', state_id)])['id']
            country_group_ids = self.env['res.country.group'].search(
                [('country_ids', 'in', country_id)])
            for country_group_id in country_group_ids:
                potential_region = self.env['sales.team.region'].search(
                    [('country_groups', 'in', country_group_id.id)])
                # cycle till we hit one
                if potential_region:
                    cg_region_id = potential_region.id
                    break
            region_id = s_region_id or c_region_id or cg_region_id
            if region_id:
                team = self.env['crm.team'].search([('region_id', '=',
                                                     region_id)])
                if team:
                    return team
        # return 0
        return self.env['crm.team']

    @api.model
    def lookup_team(self, state_id=False, customer=False, country_id=False):
        return self._lookup_team(state_id, customer,
                                 country_id).id or self._default_team()

#    @api.one
#    @api.depends('state_id', 'customer')
    @api.model
    def _default_team(self):
    #def _default_team(self, state_id, customer):
        # this should set team_id for creation via xmlrpc
        #state_id = self.env.context.get('state_id', False)
        #customer = self.env.context.get('customer', False)
        #state_id = self.state_id
        #customer = self.customer
        #self = self.with_context(self._context)
        #partner = self.pool.get('res.partner').browse(self._cr,self._uid,self._context)
        #state_id = partner.state_id
        #customer = partner.customer
        #import pdb
        #pdb.set_trace()
        #if state_id and customer:

        #team_id = self._lookup_team(state_id, customer)
        #if team_id:
        #    return team_id
        #if customer:
            #return 0 #need external id of default crm.team.id
            #return self.env['ir.property'].get('','sales.team.region')
            # default to odoo builtin sales team as customer requires one
            #return self.env['ir.property'].get('team_sales_department','crm.team')
        # https://github.com/odoo/odoo/blob/8.0/openerp/addons/base/ir/ir_model.py#L940
        return self.env['ir.model.data'].xmlid_to_res_id(
            'sales_team.team_sales_department')
        #return False
        #return self.env['crm.team'].search([('region_id','=',0)])

    @api.model
    @api.constrains('team_id', 'customer')
    def _require_team(self):
        #for partner in self.browse():
        for record in self:
            #if partner.customer and not partner.team_id.id:
                #return False
            #if self.env['res.users'].has_group('base.group_multi_salesteams') and record.customer and not record.team_id.id:
            if record.customer and not record.team_id.id:
                raise ValidationError("Customers require a valid Sales Team."
                                      " (%s)" % record.team_id)
        #return True

    # added due to Error triggered during 8.0 database update 20150320:
    #   Error: 'boolean' object has no attribute '_fnct_search'" while parsing
    #   /home/openerp/azi-odoo-modules/sales_team_region/sales_team_view.xml:31
    @api.model
    def _st_search(self):
        return [('id', 'in', [])]

#    team_id = fields.Many2one('crm.team', 'Sales Team', default=lambda self: self.with_context(self._context)._default_team(self.state_id, self.customer))
    team_id = fields.Many2one('crm.team', 'Sales Team')
    state_trigger = fields.Boolean(store=False, default=False,
                                   search='_st_search')

    @api.multi
    def onchange_state(self, state_id=False, customer=False,
                       state_trigger=False):
        if state_id:
            res = super(res_partner, self).onchange_state(state_id)
            res['value']['state_trigger'] = state_trigger
            res['value']['team_id'] = self._lookup_team(state_id, customer)
        else:
            res = {'value': {'state_trigger': False}}
        return res

    @api.multi
    def onchange_country(self, country_id=False, customer=False,
                         state_trigger=False):
        res = {'value': {'state_trigger': False}}
        if not state_trigger:
            res['value']['state_id'] = self.env[
                'res.country.state'].browse().id
            res['value']['team_id'] = self._lookup_team(customer=customer,
                                                        country_id=country_id)
        return res

    @api.multi
    def onchange_customer(self, state_id=False, country_id=False,
                          customer=False):
        if state_id:
            return self.onchange_state(state_id, customer)
        if country_id:
            return self.onchange_country(country_id, customer)


class sales_team_region_state_rel(models.Model):
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


class sales_team_region_country_rel(models.Model):
    _name = 'sales.team.region.country.rel'

    region_id = fields.Many2one('sales.team.region', 'Sales Region',
                                required=True, translate=True,
                                ondelete='cascade')
    country_id = fields.Many2one('res.country', 'Country', required=True,
                                 translate=True)

    _sql_constraints = [
        ('rel_country_uniq', 'unique(country_id)',
         _('A region with the same country already exists [rel_country_uniq]')
         ),
    ]


class sales_team_region_country_group_rel(models.Model):
    _name = 'sales.team.region.country.group.rel'

    region_id = fields.Many2one('sales.team.region', 'Sales Region',
                                required=True, translate=True,
                                ondelete='cascade')
    country_group_id = fields.Many2one('res.country.group', 'Country Group',
                                       required=True, translate=True)

    _sql_constraints = [
        ('rel_country_group_uniq', 'unique(country_group_id)',
         _('A region with the same country group already exists'
           ' [rel_country_group_uniq]')),
    ]


class sales_team_region(models.Model):
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
                raise ValidationError("Sales regions require a valid region"
                                      " definition. Please select at least one"
                                      " state, country, or country group.")

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
