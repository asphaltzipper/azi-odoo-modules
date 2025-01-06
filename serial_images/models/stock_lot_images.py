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
        comodel_name='stock.lot',
        string='Serial',
        required=False)

    def action_open_line(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            'serial_images.action_form_stock_lot_images')
        action['res_id'] = self.id
        return action
