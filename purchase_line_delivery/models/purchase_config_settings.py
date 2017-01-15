# -*- coding: utf-8 -*-
# Copyright 2015-2017 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseConfigSettings(models.TransientModel):
    _inherit = 'purchase.config.settings'

   po_carrier_id = fields.Many2one(
        string='Default Purchase Carrier',
        comodel_name='delivery.carrier',
        ondelete='restrict',
        help="Delivery carrier to use on purchase orders when the supplier has none.")

    @api.multi
    def set_po_carrier(self):
        self.env['ir.values'].sudo().set_default('purchase.config.settings', "po_carrier_id", self.po_carrier_id.id)
 
