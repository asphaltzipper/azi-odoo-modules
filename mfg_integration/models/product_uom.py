# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductUoMCategory(models.Model):
    _inherit = 'product.uom.categ'

    is_continuous = fields.Boolean(string='Continuous')
