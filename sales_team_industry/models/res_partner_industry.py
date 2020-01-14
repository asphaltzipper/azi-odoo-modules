# -*- coding: utf-8 -*-
# Copyright 2016 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PartnerIndustry(models.Model):
    _inherit = 'res.partner.industry'

    name = fields.Char('Partner Industry', required=True, translate=True)
    color = fields.Integer('Color Index')
