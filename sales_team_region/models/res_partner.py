# -*- coding: utf-8 -*-
# Copyright 2014-2016 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    team_ids = fields.Many2many('crm.team', column1='team_id',
                                column2='partner_id', string='Sales Teams')
