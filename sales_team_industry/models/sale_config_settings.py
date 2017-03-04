# -*- coding: utf-8 -*-
# Copyright 2014-2017 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleConfiguration(models.TransientModel):
    _inherit = 'sale.config.settings'

    require_industry = fields.Selection(
        [(0, "Don't require industry"),
         (1, 'Require industry on partner and team')],
        string='Require Industry',
        help='Partner must reference an industry, sales team must reference'
        ' one or more')

    @api.multi
    def set_require_industry(self):
        self.env['ir.values'].sudo().set_default(
            'sale.config.settings', "require_industry", self.require_industry)
