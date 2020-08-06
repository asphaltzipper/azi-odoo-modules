# -*- coding: utf-8 -*-
from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    shelf_ids = fields.Many2many(
        comodel_name='stock.shelf',
        string="Stock Shelves", copy=False)

    shelf_list = fields.Char(
        string="Shelf List",
        compute='_compute_shelf_list')

    @api.depends('shelf_ids')
    def _compute_shelf_list(self):
        for tmpl in self:
            if tmpl.shelf_ids:
                tmpl.shelf_list = ", ".join(tmpl.shelf_ids.mapped('name'))
