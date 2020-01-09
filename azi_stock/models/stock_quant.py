# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class StockQuant(models.Model):
    _inherit = "stock.quant"

    category_id = fields.Many2one(
        comodel_name='product.category',
        related='product_id.categ_id',
        readonly=True,
        store=True)

    @api.constrains('location_id', 'product_id', 'lot_id')
    def _check_internal_location_with_serial_product(self):
        if self.location_id.usage == 'internal'and self.product_id.tracking == 'serial':
            if self.lot_id:
                raise ValidationError('Serial number %s is not available in stock location %s' %
                                      (self.lot_id.name, self.location_id.display_name))
            else:
                raise ValidationError('Serial tracked item %s is not available in stock location %s' %
                                      (self.product_id.display_name, self.location_id.display_name))
