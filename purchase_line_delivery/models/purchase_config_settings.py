# -*- coding: utf-8 -*-
# Copyright 2015-2017 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    po_carrier_id = fields.Many2one(
        string='Default Purchase Carrier',
        comodel_name='delivery.carrier',
        ondelete='restrict',
        help="Delivery carrier to use on purchase orders when the supplier has none.")
 
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        po_carrier = self.env['ir.config_parameter'].sudo().get_param('purchase_line_delivery.po_carrier_id')
        res.update(po_carrier_id=po_carrier and int(po_carrier) or False)
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('purchase_line_delivery.po_carrier_id', self.po_carrier_id.id)
