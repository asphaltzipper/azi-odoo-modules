# -*- coding: utf-8 -*-
# Copyright 2014-2016 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import ValidationError
from openerp.tools.translate import _


class Partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _lookup_team(self, state_id=False, customer=False, country_id=False,
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
                            ('partner_industries', 'in', industry_id)]
                else:
                    domain = [('region_id', '=', region_id)]
                r_teams = self.env['crm.team'].search(domain)
                for team in r_teams:
                    if team and team.id:
                        teams.add(team)
            if teams:
                return [(6, 0, [t.id for t in teams or []])]

    @api.model
    def lookup_team(self, state_id=False, customer=False, country_id=False,
                    industry_id=False):
        return self._lookup_team(state_id, customer, country_id,
                                 industry_id) or self._default_team()

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
                                        " (%s)") % record.team_id)

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
    @api.depends('customer', 'partner_industry', 'auto_assign_team')
    def onchange_state(self, state_trigger=True):
        if self.state_id:
            super(Partner, self).onchange_state()
            self.state_trigger = state_trigger
            if self.auto_assign_team:
                self.team_ids = self._lookup_team(
                    self.state_id.id, self.customer,
                    industry_id=self.partner_industry.id)
        else:
            self.state_trigger = False

    @api.onchange('country_id')
    @api.depends('customer', 'state_trigger', 'partner_industry',
                 'auto_assign_team')
    def onchange_country(self):
        if not self.state_trigger:
            self.state_id = self.env['res.country.state'].browse().id
            if self.auto_assign_team:
                self.team_ids = self._lookup_team(
                    customer=self.customer, country_id=self.country_id.id,
                    industry_id=self.partner_industry.id)
        self.state_trigger = False

    @api.onchange('customer', 'partner_industry', 'auto_assign_team')
    @api.depends('state_id', 'country_id')
    def onchange_customer(self):
        if self.state_id:
            return self.onchange_state(False)
        if self.country_id:
            self.state_trigger = False
            return self.onchange_country()
