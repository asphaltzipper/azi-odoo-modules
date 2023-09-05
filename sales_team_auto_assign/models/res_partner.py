# -*- coding: utf-8 -*-
# Copyright 2014-2017 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, registry
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class Partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def lookup_team(self, state_id=False, customer=False, country_id=False, industry_id=False):
        if (state_id or country_id) and customer:
            region_ids = set()
            teams = set()
            if not country_id:
                country_id = self.env['res.country.state'].browse(state_id).country_id.id
            c_regions = self.env['crm.team.region'].search([('countries', 'in', country_id)])
            for c_region in c_regions:
                if c_region and c_region.id:
                    region_ids.add(c_region.id)
            if state_id:
                s_regions = self.env['crm.team.region'].search([('states', 'in', state_id)])
                for s_region in s_regions:
                    if s_region and s_region.id:
                        region_ids.add(s_region.id)
            country_group_ids = self.env['res.country.group'].search([('country_ids', 'in', country_id)])
            for country_group_id in country_group_ids:
                g_regions = self.env['crm.team.region'].search([('country_groups', 'in', country_group_id.id)])
                for g_region in g_regions:
                    if g_region and g_region.id:
                        region_ids.add(g_region.id)
            for region_id in region_ids:
                if industry_id:
                    domain = [('region_id', '=', region_id),
                              '|', ('partner_industries', 'in', industry_id),
                              ('all_industries', '=', True)]
                else:
                    domain = [('region_id', '=', region_id)]
                r_teams = self.env['crm.team'].search(domain)
                for team in r_teams:
                    if team and team.id:
                        teams.add(team)
            return [(6, 0, [t.id for t in teams or
                            []])] if teams else self._default_team()
        elif customer:
            return self._default_team()
        else:
            return [(6, 0, [])]

    @api.model
    def _default_team(self):
        return [(6, 0, [self.env['ir.model.data']._xmlid_to_res_id('sales_team.team_sales_department')])]

    @api.model
    @api.constrains('team_ids', 'customer_rank')
    def _require_team(self):
        for record in self:
            if (record.customer_rank > 0 and not record.team_ids and not
                    record.parent_id):
                raise ValidationError(_("Customers require a valid Sales Team."
                                        " \n\nEnsure a Sales Region is"
                                        " assigned to each team or disable"
                                        " Auto Assign Team(s) to remember"
                                        " manual assignment."))

    @api.model
    def _st_search(self):
        return [('id', 'in', [])]

    state_trigger = fields.Boolean(store=False, default=False,
                                   search='_st_search')
    auto_assign_team = fields.Boolean(
        'Auto Assign Team(s)', help="The auto assign field allows for sales"
        " team auto assignment. Disable to remember manual assignment.",
        default=True)

    @api.onchange('state_id')
    @api.depends('customer_rank', 'industry_id', 'auto_assign_team')
    def onchange_state(self, state_trigger=True):
        if self.state_id:
            self.state_trigger = state_trigger
            if self.auto_assign_team:
                self.team_ids = self.lookup_team(
                    self.state_id.id, self.customer_rank > 0,
                    industry_id=self.industry_id.id)
        else:
            self.state_trigger = False

    @api.onchange('country_id')
    @api.depends('customer_rank', 'state_trigger', 'industry_id', 'auto_assign_team')
    def onchange_country(self):
        if not self.state_trigger:
            self.state_id = self.env['res.country.state'].browse().id
            customer = self.customer_rank > 0
            if self.auto_assign_team:
                self.team_ids = self.lookup_team(customer=customer, country_id=self.country_id.id,
                                                 industry_id=self.industry_id.id)
        self.state_trigger = False

    @api.onchange('customer_rank', 'industry_id', 'auto_assign_team')
    @api.depends('state_id', 'country_id')
    def onchange_customer(self):
        if self.state_id:
            return self.onchange_state(False)
        if self.country_id:
            self.state_trigger = False
            return self.onchange_country()

    @api.model
    def _ensure_team(self, vals):
        state_id = (vals.get('state_id') if 'state_id' in vals else None or
                    self.state_id.id if hasattr(self, 'state_id') else None)
        customer = (vals.get('customer_rank') if 'customer_rank' in vals else None or
                    self.customer_rank if hasattr(self, 'customer_rank') else None)
        country_id = (vals.get('country_id') if 'country_id' in vals else None
                      or self.country_id.id if hasattr(self, 'country_id') else
                      None)
        industry_id = (vals.get('industry_id') if 'industry_id' in vals else
                       None or self.industry_id.id if hasattr(
                           self, 'industry_id') else None)
        return self.lookup_team(state_id, customer > 0, country_id, industry_id)

    def write(self, vals):
        for partner in self:
            if (vals.get('auto_assign_team') or partner.auto_assign_team and
                    'auto_assign_team' not in vals):
                vals['team_ids'] = partner._ensure_team(vals)
        return super(Partner, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('auto_assign_team'):
                vals['team_ids'] = self._ensure_team(vals)
        return super(Partner, self).create(vals_list)

    def _assign_all_customers(self, use_new_cursor=False, company_id=False):
        """ Assign sales team(s) to customers.
            This is appropriate for batch jobs only.
        """
        if use_new_cursor:
            cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=cr))

        domain = company_id and [('company_id', '=', company_id)] or []
        domain += [('customer_rank', '>', 0)]
        for record in self.env['res.partner'].search(domain):
            if record.auto_assign_team:
                record.team_ids = self.lookup_team(
                    state_id=record.state_id.id,
                    customer=record.customer > 0,
                    country_id=record.country_id.id,
                    industry_id=record.industry_id.id)

        if use_new_cursor:
            cr.commit()
            cr.close()
        return {}
