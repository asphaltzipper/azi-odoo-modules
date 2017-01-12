# -*- coding: utf-8 -*-
# Copyright 2015-2017 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseConfigSettings(models.TransientModel):
    _inherit = 'purchase.config.settings'

    default_carrier_id = fields.Many2one(
        string='Default Purchase Carrier',
        comodel_name='delivery.carrier',
        ondelete='restrict',
        default_model='purchase.order',
        help="Default delivery carrier for purchase order when the selected supplier has none.")
