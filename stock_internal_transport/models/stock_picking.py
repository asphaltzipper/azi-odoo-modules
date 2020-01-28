# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    transport = fields.Boolean(string="Transportation")


class StockPicking(models.Model):
    _inherit = "stock.picking"

    type_transport = fields.Boolean(
        string='Transport',
        related='picking_type_id.transport',
        readonly=True)

    srce_contact_id = fields.Many2one(
        comodel_name='res.partner',
        string="Source Address")

    dest_contact_id = fields.Many2one(
        comodel_name='res.partner',
        string="Destination Address")

    @api.onchange('location_id')
    def onchange_location_id(self):
        if not self.type_transport:
            return
        if self.location_id.partner_id:
            self.srce_contact_id = self.location_id.partner_id

    @api.onchange('location_dest_id')
    def onchange_location_dest_id(self):
        if not self.type_transport:
            return
        if self.location_dest_id.partner_id:
            self.dest_contact_id = self.location_dest_id.partner_id
