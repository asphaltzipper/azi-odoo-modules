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
