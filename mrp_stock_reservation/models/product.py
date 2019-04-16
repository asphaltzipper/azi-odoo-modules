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
    _inherit = "product.product"

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

    _mrp_reservation_barcode_scanned = fields.Char(
        string="Barcode Scanned",
        help="Value of the last barcode scanned.",
        store=False)

    @api.depends('stock_quant_ids', 'stock_move_ids')
    def _compute_qty_reserved(self):
        for product in self:
            product.qty_reserved = sum(
                product.stock_quant_ids.filtered(
                    lambda r: r.reservation_id and r.reservation_id.state not in ['done', 'cancel']
                ).mapped('qty')
            )

    @api.multi
    def action_mrp_reservation_form(self):
        self.ensure_one()
        action = self.env.ref('mrp_stock_reservation.action_mrp_stock_reservation').read()[0]
        action['res_id'] = self.id
        return action

    @api.model
    def mrp_res_barcode(self, barcode, prod_id):
        new_prod = self.search(['|', ('mfg_code', '=', barcode), ('barcode', '=', barcode)], limit=1)
        if new_prod:
            # return an action that will load a new product in the form
            # this is done in the javascript barcode handler function
            return new_prod.action_mrp_reservation_form()

        mo = self.env['mrp.production'].search([('name', '=', barcode)], limit=1)
        if not mo:
            raise UserError("Unknown Barcode: %s" % (barcode,))
        domain = [
            ('product_id', '=', prod_id),
            ('raw_material_production_id', '=', mo.id)
        ]
        moves = self.env['stock.move'].search(domain)
        for move in moves:
            move.action_assign()
