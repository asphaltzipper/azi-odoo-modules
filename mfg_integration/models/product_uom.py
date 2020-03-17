# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductUoMCategory(models.Model):
    _inherit = 'uom.category'

    is_continuous = fields.Boolean(string='Continuous')
