# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def action_mrp_reservation_form(self):
        self.ensure_one()
        if len(self.product_variant_ids) > 1:
            raise UserError(_("This product has variants.  Go to one of the variants and choose Mfg Reservations"))
        return self.product_variant_ids[0].action_mrp_reservation_form()


class ProductProduct(models.Model):
    _name = "product.product"
    _inherit = ['product.product', 'barcodes.barcode_events_mixin']

    mfg_demand_ids = fields.One2many(
        comodel_name='stock.move',
        inverse_name='product_id',
        domain=[
            ('raw_material_production_id', '!=', False),
            ('state', 'in', ['confirmed', 'assigned'])],
        readonly=True)

    qty_reserved = fields.Float(
        string='Reserved',
        compute='_compute_qty_reserved')

    _barcode_scanned = fields.Char(
        string="Barcode Scanned",
        help="Value of the last barcode scanned.",
        store=False)

    @api.depends('stock_quant_ids', 'stock_move_ids')
    def _compute_qty_reserved(self):
        for product in self:
            product.qty_reserved = sum(
                product.stock_quant_ids.mapped('reserved_quantity')
            )

    def action_mrp_reservation_form(self):
        self.ensure_one()
        action = self.env.ref('mrp_stock_reservation.action_mrp_stock_reservation').read()[0]
        action['res_id'] = self.id
        return action

    def on_barcode_scanned(self, barcode):
        new_prod = self.search(['|', ('mfg_code', '=', barcode), ('barcode', '=', barcode)], limit=1)
        if new_prod:
            return new_prod.action_mrp_reservation_form()
        mo = self.env['mrp.production'].search([('name', '=', barcode)], limit=1)
        if not mo:
            raise UserError("Unknown Barcode: %s" % (barcode,))
        product_id = self.id or self._origin.id
        domain = [
            ('product_id', '=', product_id),
            ('raw_material_production_id', '=', mo.id)
        ]
        moves = self.env['stock.move'].search(domain)
        for move in moves:
            move._action_assign()
