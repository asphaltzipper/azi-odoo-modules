# -*- coding: utf-8 -*-
# Copyright 2014-2016 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    partner_industry = fields.Many2one('res.partner.industry', 'Industry')
