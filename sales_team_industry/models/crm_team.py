# -*- coding: utf-8 -*-
# Copyright 2016 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    @api.model
    @api.constrains('partner_industries', 'all_industries')
    def _require_industry(self):
        self.ensure_one()
        industry_required = 0
        settings_record = self.env['sale.config.settings'].search([])
        if settings_record:
            industry_required = settings_record[0].require_industry
        if not industry_required:
            return
        if not (self.partner_industries or self.all_industries):
            raise ValidationError(_("Teams require a valid Industry"))

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

    # @api.model
    # @api.onchange('all_industries', 'partner_industries')
    # def onchange_industry(self):
    #     if not self.env['sales.config.settings'][0].require_industry:
    #         return
    #     if not self.all_industries and not self.partner_industries:
    #         raise ValidationError(_("Teams require a valid Industry"))
