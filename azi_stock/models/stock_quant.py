# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


class StockQuant(models.Model):
    _inherit = "stock.quant"

    category_id = fields.Many2one(
        comodel_name='product.category',
        related='product_id.categ_id',
        readonly=True,
        store=True)

    @api.model
    def _quant_create_from_move(
            self, qty, move, lot_id=False, owner_id=False,
            src_package_id=False, dest_package_id=False,
            force_location_from=False, force_location_to=False):

        # prevent negative quants for serial tracked products
        if move.location_id.usage == 'internal'\
                and move.product_id.tracking == 'serial':
            if lot_id:
                raise UserError(
                    'Serial number %s is not available in stock location %s' %
                    (self.env['stock.production.lot'].browse(lot_id).name,
                     force_location_from and force_location_from.display_name or move.location_id.name)
                )
            else:
                raise UserError(
                    'Serial tracked item %s is not available in stock location %s' %
                    (move.product_id.display_name,
                     force_location_from and force_location_from.display_name or move.location_id.name)
                )

        return super(StockQuant, self)._quant_create_from_move(
            qty, move, lot_id, owner_id, src_package_id, dest_package_id,
            force_location_from, force_location_to)
