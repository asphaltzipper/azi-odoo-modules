# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    serial_images_ids = fields.Many2many(
        comodel_name='stock.lot.images',
        string="Build Books")
