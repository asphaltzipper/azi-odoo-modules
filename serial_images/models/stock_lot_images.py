# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockLotImages(models.Model):
    _name = 'stock.lot.images'
    _description = 'Serialized Product Documentation Images'

    name = fields.Char(string='Name', required=True)

    note = fields.Text(string='Note', required=True)

    attachment_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        domain=[('res_model', '=', 'stock.lot.images'), ('type', '=', 'binary')],
        auto_join=True,
        string="Documents")

    lot_ids = fields.Many2many(
        comodel_name='stock.production.lot',
        string='Serial',
        required=False)

    @api.multi
    def action_open_line(self):
        self.ensure_one()
        action = self.env.ref('serial_images.action_form_stock_lot_images').read()[0]
        action['res_id'] = self.id
        return action
