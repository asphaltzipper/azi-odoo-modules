# -*- coding: utf-8 -*-
# Copyright 2014-2017 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleConfigSettings(models.TransientModel):
    _inherit = 'sale.config.settings'

    auto_assign_team = fields.Boolean(
        'Auto Assign Team(s)', help="The auto assign field allows for sales"
        " team auto assignment on a customer. Disable to remember manual"
        " assignment by default.",
        default=True)

    @api.multi
    def set_auto_assign_team(self):
        self.env['ir.values'].sudo().set_default('sale.config.settings',
                                                 "auto_assign_team",
                                                 self.auto_assign_team)
