# -*- coding: utf-8 -*-
# Copyright 2014-2017 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    require_industry = fields.Selection(
        [("0", "Don't require industry"),
         ("1", 'Require industry on a customer and a team')],
        string='Require Industry',
        help='Partner must reference an industry, sales team must reference'
        ' one or more')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(require_industry=self.env['ir.config_parameter'].sudo().get_param(
                'sales_team_industry.require_industry', default="0"))
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param(
            'sales_team_industry.require_industry', self.require_industry)
