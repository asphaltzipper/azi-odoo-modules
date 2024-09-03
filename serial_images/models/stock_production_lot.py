# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockLot(models.Model):
    _inherit = 'stock.lot'

    serial_images_ids = fields.Many2many(
        comodel_name='stock.lot.images',
        string="Build Books")
