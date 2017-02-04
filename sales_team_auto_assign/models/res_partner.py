# -*- coding: utf-8 -*-
# Copyright 2014-2016 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class Partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def lookup_team(self, state_id=False, customer=False, country_id=False,
                     industry_id=False):
        if (state_id or country_id) and customer:
            domain = []
            region_ids = set()
            teams = set()
            if not country_id:
                country_id = self.env['res.country.state'].browse(
                    state_id)['country_id']['id']
            c_regions = self.env['crm.team.region'].search(
                [('countries', 'in', country_id)])
            for c_region in c_regions:
                if c_region and c_region.id:
                    region_ids.add(c_region.id)
            if state_id:
                s_regions = self.env['crm.team.region'].search(
                    [('states', 'in', state_id)])
                for s_region in s_regions:
                    if s_region and s_region.id:
                        region_ids.add(s_region.id)
            country_group_ids = self.env['res.country.group'].search(
                [('country_ids', 'in', country_id)])
            for country_group_id in country_group_ids:
                g_regions = self.env['crm.team.region'].search(
                    [('country_groups', 'in', country_group_id.id)])
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
        # https://github.com/odoo/odoo/blob/8.0/openerp/addons/base/ir/ir_model.py#L940
        return [(6, 0, [self.env['ir.model.data'].xmlid_to_res_id(
            'sales_team.team_sales_department')])]

    @api.model
    @api.constrains('team_ids', 'customer')
    def _require_team(self):
        for record in self:
            if record.customer and not record.team_ids:
                raise ValidationError(_("Customers require a valid Sales Team."
                                        " (%s)\n\nIf you have selected one or"
                                        " more teams, ensure a Sales Region is"
                                        " assigned to each team or disable"
                                        " Auto Assign Team(s).") %
                                      record.team_ids)

    # added due to Error triggered during 8.0 database update 20150320:
    #   Error: 'boolean' object has no attribute '_fnct_search'" while parsing
    #   /home/openerp/azi-odoo-modules/sales_team_region/sales_team_view.xml:31
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
    @api.depends('customer', 'industry_id', 'auto_assign_team')
    def onchange_state(self, state_trigger=True):
        if self.state_id:
            self.state_trigger = state_trigger
            if self.auto_assign_team:
                self.team_ids = self.lookup_team(
                    self.state_id.id, self.customer,
                    industry_id=self.industry_id.id)
        else:
            self.state_trigger = False

    @api.onchange('country_id')
    @api.depends('customer', 'state_trigger', 'industry_id',
                 'auto_assign_team')
    def onchange_country(self):
        if not self.state_trigger:
            self.state_id = self.env['res.country.state'].browse().id
            if self.auto_assign_team:
                self.team_ids = self.lookup_team(
                    customer=self.customer, country_id=self.country_id.id,
                    industry_id=self.industry_id.id)
        self.state_trigger = False

    @api.onchange('customer', 'industry_id', 'auto_assign_team')
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
        customer = (vals.get('customer') if 'customer' in vals else None or
                    self.customer if hasattr(self, 'customer') else None)
        country_id = (vals.get('country_id') if 'country_id' in vals else None
                      or self.country_id.id if hasattr(self, 'country_id') else
                      None)
        industry_id = (vals.get('industry_id') if 'industry_id' in vals else
                       None or self.industry_id.id if hasattr(
                           self, 'industry_id') else None)
        return self.lookup_team(state_id, customer, country_id, industry_id)

    @api.multi
    def write(self, vals):
        if (vals.get('auto_assign_team') or self.auto_assign_team and
                'auto_assign_team' not in vals):
            vals['team_ids'] = self._ensure_team(vals)
        return super(Partner, self).write(vals)

    @api.model
    def create(self, vals):
        if vals.get('auto_assign_team'):
            vals['team_ids'] = self._ensure_team(vals)
        return super(Partner, self).create(vals)
