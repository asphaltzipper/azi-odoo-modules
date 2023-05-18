# -*- coding: utf-8 -*-
# Copyright 2016-2017 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    partner_industries = fields.Many2many(
        comodel_name='res.partner.industry',
        column1='partner_id',
        column2='team_id',
        string='Partner Industries')

    all_industries = fields.Boolean(
        string='All Industries',
        help="This field assumes all industries are to be"
        " associated with this team. Disables manual assignment on teams.",
        default=False)

    def write(self, vals):
        if int(self.env['ir.config_parameter'].sudo().get_param('sales_team_industry.require_industry')):
            if (not ((vals.get('partner_industries') or
                    vals.get('all_industries')) or
                    (self.partner_industries and 'partner_industries' not in
                     vals or self.all_industries and 'all_industries' not in
                     vals))) or (vals.get('partner_industries') and not vals['partner_industries'][0][2] and not vals.get('all_industries')):
                raise ValidationError(_("Teams require a valid Industry."))
        return super(CrmTeam, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        if int(self.env['ir.config_parameter'].sudo().get_param('sales_team_industry.require_industry')):
            for vals in vals_list:
                if not (vals.get('partner_industries') or
                        vals.get('all_industries')):
                    raise ValidationError(_("Teams require a valid Industry."))
        return super(CrmTeam, self).create(vals_list)
