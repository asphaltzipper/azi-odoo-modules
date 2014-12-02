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

class crm_case_section(models.Model): # sales_team
    _inherit = 'crm.case.section'

    region_id = fields.Many2one('sales.team.region', 'Sales Region', translate=True)


class res_partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _lookup_section(self, state_id=False, customer=False, country_id=False):
        if (state_id or country_id) and customer:
            s_region_id = False
            c_region_id = False
            cg_region_id = False
            if not country_id:
                country_id = self.env['res.country.state'].browse(state_id)['country_id']['id']
            c_region_id = self.env['sales.team.region'].search([('countries','in',country_id)])['id']
            if state_id:
                s_region_id = self.env['sales.team.region'].search([('states','in',state_id)])['id']
            country_group_ids = self.env['res.country.group'].search([('country_ids','in',country_id)])
            for country_group_id in country_group_ids:
                potential_region = self.env['sales.team.region'].search([('country_groups','in',country_group_id.id)])[0]
                # cycle till we hit one
                if potential_region:
                    cg_region_id = potential_region.id
                    break
            region_id = s_region_id or c_region_id or cg_region_id
            if region_id:
                section_id = self.env['crm.case.section'].search([('region_id','=',region_id)])
                if section_id:
                    return section_id
        return 0


    #@api.one
    #@api.depends('state_id', 'customer')
    @api.model
    #def _default_section(self):
    def _default_section(self, state_id, customer):
        # this should set section_id for creation via xmlrpc
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
        section_id = self._lookup_section(state_id, customer)
        if section_id:
            return section_id
        if customer:
            #return 0 #need external id of default crm.case.section.id
            #return self.env['ir.property'].get('','sales.team.region')
            # default to odoo builtin sales team as customer requires one
            return self.env['ir.property'].get('section_sales_department','crm.case.section')
        return False
        #return self.env['crm.case.section'].search([('region_id','=',0)])

    @api.model
    @api.constrains('section_id','customer')
    def _require_section(self):
        #for partner in self.browse():
        for record in self:
            #if partner.customer and not partner.section_id.id:
                #return False
            if record.customer and not record.section_id.id:
                raise ValidationError("Customers require a valid Sales Team. (%s)" % record.section_id)
        #return True

    #section_id = fields.Many2one('crm.case.section', 'Sales Team', default=lambda self: self.with_context(self._context)._default_section(self.state_id, self.customer))
    section_id = fields.Many2one('crm.case.section', 'Sales Team') 
    state_trigger = fields.Boolean(store=False, default=False)


    @api.multi
    def onchange_state(self, state_id=False, customer=False):
        res = super(res_partner, self).onchange_state(state_id)
        #if state_id and customer:
            #section_id = self._default_section(state_id)
            #self = self.with_context(state_id=state_id, customer=customer)
            #self.state_id = state_id
            #self.customer = customer
            #test = self.browse()[0]
            #section_id = test._default_section()
            #section_id = self._lookup_section(state_id, customer)
            #if section_id:
                #res['value']['section_id'] = section_id
        if res:
            res['value']['section_id'] = self._lookup_section(state_id, customer)
            res['value']['state_trigger'] = True
        return res

    @api.multi
    def onchange_country(self, country_id=False, customer=False, state_trigger=False):
        if not state_trigger:
            return {'value': {'section_id': self._lookup_section(customer=customer, country_id=country_id)}}
        return {'value': {'state_trigger': False}}


class sales_team_region_state_rel(models.Model):
    _name = 'sales.team.region.state.rel'

    region_id = fields.Many2one('sales.team.region', 'Sales Region', required=True, translate=True, ondelete='cascade')
    state_id = fields.Many2one('res.country.state', 'State', required=True, translate=True)

    _sql_constraints = [
        ('rel_state_uniq', 'unique(state_id)', _('A region with the same state already exists [rel_state_uniq]')),
    ]


class sales_team_region_country_rel(models.Model):
    _name = 'sales.team.region.country.rel'

    region_id = fields.Many2one('sales.team.region', 'Sales Region', required=True, translate=True, ondelete='cascade')
    country_id = fields.Many2one('res.country', 'Country', required=True, translate=True)

    _sql_constraints = [
        ('rel_country_uniq', 'unique(country_id)', _('A region with the same country already exists [rel_country_uniq]')),
    ]


class sales_team_region_country_group_rel(models.Model):
    _name = 'sales.team.region.country.group.rel'

    region_id = fields.Many2one('sales.team.region', 'Sales Region', required=True, translate=True, ondelete='cascade')
    country_group_id = fields.Many2one('res.country.group', 'Country Group', required=True, translate=True)

    _sql_constraints = [
        ('rel_country_group_uniq', 'unique(country_id)', _('A region with the same country group already exists [rel_country_group_uniq]')),
    ]


class sales_team_region(models.Model):
    _name = 'sales.team.region'

    name = fields.Char('Sales Region', required=True, translate=True)
    states = fields.Many2many('res.country.state', 'sales_team_region_state_rel', 'region_id', 'state_id')
    countries = fields.Many2many('res.country', 'sales_team_region_country_rel', 'region_id', 'country_id')
    country_groups = fields.Many2many('res.country.group', 'sales_team_region_country_group_rel', 'region_id', 'country_group_id')

    @api.model
    @api.constrains('states', 'countries', 'country_groups')
    def _require_region_definition(self):
        for record in self:
            if not (record.states or record.countries or record.country_groups):
                raise ValidationError("Sales regions require a valid region definition. Please select at least one state, country, or country group.")

    @api.multi
    def onchange_region(self, states=False, countries=False, country_groups=False):
        state_ids = set()
        country_ids = set()
        country_group_ids = set()
        # add existing regions for domain exclusion
        # look at optimizing this in the future
        for record in self.env['sales.team.region'].search([]):
            for state in record.states:
                state_ids.add(state.id)
            for country in record.countries:
                country_ids.add(country.id)
                for state in self.env['res.country.state'].search([('country_id','=',country.id)]):
                    state_ids.add(state.id) # exclude states of countries
            for country_group in record.country_groups:
                country_group_ids.add(country_group.id)
                for country in country_group.country_ids:
                    country_ids.add(country.id) # countries of country_groups
                    for state in self.env['res.country.state'].search([('country_id','=',country.id)]):
                        state_ids.add(state.id) # states of countries of etc.
        # add currently selected regions for domain exclusion
        for state_id in states[0][2]:
            for state in self.env['res.country.state'].browse(state_id):
                country_ids.add(state.country_id.id)
                for country_group in self.env['res.country.group'].search([('country_ids','in',state.country_id.id)]):
                    country_group_ids.add(country_group.id)
        for country_id in countries[0][2]:
            for state in self.env['res.country.state'].search([('country_id','=',country_id)]):
                state_ids.add(state.id)
            for country_group in self.env['res.country.group'].search([('country_ids','in',country_id)]):
                country_group_ids.add(country_group.id)
        for country_group_id in country_groups[0][2]:
            for country in self.env['res.country.group'].browse(country_group_id)['country_ids']:
                country_ids.add(country.id)
                for state in self.env['res.country.state'].search([('country_id','=',country.id)]):
                    state_ids.add(state.id)
        return {'domain': {'states': [('id', 'not in', list(state_ids))], 'countries': [('id', 'not in', list(country_ids))], 'country_groups': [('id', 'not in', list(country_group_ids))]}}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
