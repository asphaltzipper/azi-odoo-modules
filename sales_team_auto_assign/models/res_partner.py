# -*- coding: utf-8 -*-
# Copyright 2014-2017 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _, exceptions, registry
from odoo.exceptions import ValidationError
import threading

RUNTHREAD = False


class Partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def lookup_team(self, state_id=False, is_customer=False, country_id=False, industry_id=False):
        if (state_id or country_id) and is_customer:
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
        elif is_customer:
            return self._default_team()
        else:
            return [(6, 0, [])]

    @api.model
    def _default_team(self):
        return [(6, 0, [self.env['ir.model.data']._xmlid_to_res_id('sales_team.team_sales_department')])]

    @api.model
    @api.constrains('team_ids', 'customer_rank', 'auto_assign_team', 'parent_id')
    def _require_team(self):
        for record in self:
            if (
                record.customer_rank > 0
                and not record.team_ids
                and not record.auto_assign_team
                and not record.parent_id
            ):
                raise ValidationError(_(
                    "Customers require a valid Sales Team. \n\nEnsure a Sales Region is"
                    " assigned to each team or disable Auto Assign Team(s) to remember"
                    " manual assignment."
                ))

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
                    state_id=self.state_id.id,
                    is_customer=self.customer_rank > 0,
                    industry_id=self.industry_id.id,
                )
                if len(self.team_ids) == 1:
                    self.team_id = self.team_ids
        else:
            self.state_trigger = False

    @api.onchange('country_id')
    @api.depends('customer_rank', 'state_trigger', 'industry_id', 'auto_assign_team')
    def onchange_country(self):
        if not self.state_trigger:
            self.state_id = self.env['res.country.state'].browse().id
            customer = self.customer_rank > 0
            if self.auto_assign_team:
                self.team_ids = self.lookup_team(
                    is_customer=customer,
                    country_id=self.country_id.id,
                    industry_id=self.industry_id.id,
                )
                if len(self.team_ids) == 1:
                    self.team_id = self.team_ids
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
        is_rec = len(self)
        if is_rec > 1:
            self.ensure_one()
        state_id = vals.get('state_id') or is_rec and self.state_id.id
        customer_rank = vals.get('customer_rank') or is_rec and self.customer_rank
        country_id = vals.get('country_id') or is_rec and self.country_id.id
        industry_id = vals.get('industry_id') or is_rec and self.industry_id.id
        return self.lookup_team(
            state_id=state_id,
            is_customer=customer_rank>0,
            country_id=country_id,
            industry_id=industry_id,
        )

    def write(self, vals):
        for partner in self:
            if (vals.get('auto_assign_team') or partner.auto_assign_team and
                    'auto_assign_team' not in vals):
                vals['team_ids'] = partner._ensure_team(vals)
                if len(vals['team_ids'][0][2]) == 1:
                    vals['team_id'] = vals['team_ids'][0][2][0]
        return super(Partner, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('auto_assign_team'):
                vals['team_ids'] = self._ensure_team(vals)
                if len(vals['team_ids'][0][2]) == 1:
                    vals['team_id'] = vals['team_ids'][0][2][0]
        return super(Partner, self).create(vals_list)

    def assign_sales_teams(self, company_id=False, background=False):
        """
        Assign sales team(s) to customers.
        If self contains no records, operate on all appropriate customers.
        """
        records = self
        if not records:
            domain = [
                ('customer_rank', '>', 0),
                ('auto_assign_team', '=', True),
                ('is_company', '=', True),
            ]
            if company_id:
                domain += ['|', ('company_id', '=', False), ('company_id', '=', company_id)]
            records = self.search(domain)
        for record in records:
            message = ""
            if not record.auto_assign_team:
                continue
            try:
                record.team_ids = self.lookup_team(
                    state_id=record.state_id.id,
                    is_customer=record.customer_rank > 0,
                    country_id=record.country_id.id,
                    industry_id=record.industry_id.id,
                )
            except Exception as e:
                message = _("Failed to assign sales teams for %s:\n%s", record.display_name, e)
                if background:
                    self.env.user.notify_warning(
                        message=message,
                        title="Assigning Sales Teams Failed",
                        sticky=True,
                    )
                    return False
                else:
                    raise ValidationError(message)

        message = _("Finished assigning sales teams")
        self.env.user.notify_success(
            message=message,
            title="Assigning Sales Teams Complete",
            sticky=True,
        )
        return True

    def _background_assign_teams(self):
        new_cr = self.pool.cursor()
        # Bind current environment to a new cursor
        self = self.with_env(self.env(cr=new_cr))
        # Call the target method using the updated environment
        success = self.env['res.partner'].assign_sales_teams(company_id=self.env.company.id, background=True)

        # Explicitly commit the new cursor to save changes
        if success:
            new_cr.commit()
        else:
            new_cr.rollback()
        new_cr.close()

        global RUNTHREAD
        RUNTHREAD = False
        return {}

    def action_reassign_all_teams(self):
        global RUNTHREAD
        if not RUNTHREAD:
            RUNTHREAD = True
            threaded_calculation = threading.Thread(
                target=self._background_assign_teams, args=()
            )
            threaded_calculation.start()
        else:
            raise ValidationError(_('Assign Teams is already running in the background'))
        return {'type': 'ir.actions.act_window_close'}
