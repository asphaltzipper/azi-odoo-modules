# -*- coding: utf-8 -*-
# Copyright 2016 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    partner_industries = fields.Many2many('res.partner.industry',
                                          column1='partner_id',
                                          column2='team_id',
                                          string='Partner Industries')
    all_industries = fields.Boolean(
        'All Industries', help="This field assumes all industries are to be"
        " associated with this team. Disables manual assignment on teams.",
        default=False)
