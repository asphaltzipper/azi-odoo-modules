# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class SaleConfiguration(models.TransientModel):
    _inherit = 'sale.config.settings'

    require_industry = fields.Selection(
        [(0, "Don't require industry"),
         (1, 'Require industry on partner and team')],
        string='Require Industry',
        help='Partner must reference an industry, sales team must reference one or more',
        default=0)
