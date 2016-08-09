# -*- coding: utf-8 -*-
# Copyright 2014-2016 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import ValidationError


class Partner(models.Model):
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
            res = super(Partner, self).onchange_state(state_id)
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
