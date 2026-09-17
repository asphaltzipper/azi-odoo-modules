# Copyright 2014-2016 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api


class Partner(models.Model):
    _inherit = 'res.partner'

    team_ids = fields.Many2many(
        comodel_name='crm.team',
        column1='team_id',
        column2='partner_id',
        string='Sales Teams',
    )

    inherited_team_ids = fields.Many2many(
        comodel_name='crm.team',
        string='Inherited Teams',
        compute='_compute_inherited_teams',
        readonly=True,
        help="Sales teams directly assigned or inherited from the parent company"
    )

    inherited_team_id = fields.Many2one(
        comodel_name='crm.team',
        string='Inherited Team',
        compute='_compute_inherited_teams',
        readonly=True,
        help="Sales team directly assigned or inherited from the parent company"
    )

    team_lead_id = fields.Many2one(
        comodel_name='res.users',
        string='Inherited Team Lead',
        compute='_compute_inherited_teams',
        readonly=True,
        help="Leader of the sales team directly assigned or inherited from the parent company"
    )

    team_names = fields.Char(
        string='Team Names',
        compute='_compute_inherited_teams',
        readonly=True,
        help="List of sales team names directly assigned or inherited from the parent company"
    )

    team_member_names = fields.Char(
        string='Team Member Names',
        compute='_compute_inherited_teams',
        readonly=True,
        help="List of sales team member names directly assigned or inherited from the parent company"
    )

    @api.depends("parent_id", "team_id", "team_ids")
    def _compute_inherited_teams(self):
        for rec in self:
            rec.inherited_team_ids = rec.team_ids or rec.parent_id.team_ids
            rec.inherited_team_id = rec.team_id or rec.parent_id.team_id

            rec.team_lead_id = rec.inherited_team_id.user_id or rec.parent_id.team_id.user_id

            member_names = rec.inherited_team_ids.member_ids.mapped("name")
            rec.team_member_names = ", ".join(member_names)

            team_names = rec.inherited_team_ids.mapped("name")
            rec.team_names = ", ".join(team_names)
