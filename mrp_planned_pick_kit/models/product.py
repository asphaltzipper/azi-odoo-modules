# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    mfg_kit_qty = fields.Integer(
        string="Kit",
        compute='_compute_mfg_kit_qty',
        inverse='_inverse_mfg_kit_qty',
        store=True,
        track_visibility='onchange',
    )

    @api.depends('product_variant_ids', 'product_variant_ids.mfg_kit_qty')
    def _compute_mfg_kit_qty(self):
        unique_variants = self.filtered(lambda x: len(x.product_variant_ids) == 1 and x.categ_id.eng_management)
        for tmpl in unique_variants:
            tmpl.mfg_kit_qty = tmpl.product_variant_ids.mfg_kit_qty
        for tmpl in (self - unique_variants):
            tmpl.mfg_kit_qty = 0

    @api.multi
    def action_create_mfg_kit(self):
        self.ensure_one()
        if len(self.product_variant_ids) > 1:
            raise UserError(_("Can't set Kit quantity because there are"
                              " multiple variants for product %s"
                              % self.display_name))
        return self.product_variant_ids.action_create_mfg_kit()

    @api.multi
    def _inverse_mfg_kit_qty(self):
        for rec in self:
            if len(rec.product_variant_ids) > 1:
                raise UserError(_("Can't set Kit quantity because there are"
                                  " multiple variants for product %s"
                                  % rec.display_name))
            if rec.product_variant_ids:
                rec.product_variant_ids.mfg_kit_qty = rec.mfg_kit_qty


class ProductProduct(models.Model):
    _inherit = "product.product"

    mfg_kit_qty = fields.Integer(
        string="Kits",
        required=True,
        default=0,
        track_visibility='onchange',
    )

    @api.multi
    def action_create_mfg_kit(self):
        self.ensure_one()
        return self.create_mfg_kit(1.0)

    @api.multi
    def create_mfg_kit(self, quantity=1.0):
        self.ensure_one()
        if not self.bom_ids:
            raise UserError(_("Can't build a kit without a BOM"))
        if self.bom_ids[0].type == 'phantom':
            raise UserError(_("Can't build a kit for a phantom BOM"))
        kit_obj = self.env['mrp.planned.pick.kit']
        existing = kit_obj.search([
            ('user_id', '=', self.env.uid),
            ('product_id', '=', self.id),
        ])
        existing.unlink()
        quantity = quantity or 1.0
        kit_values = {
            'user_id': self.env.uid,
            'product_id': self.id,
            'product_qty': quantity,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'warehouse_id': self.env.ref('stock.warehouse0').id,
        }
        kit = kit_obj.create(kit_values)
        bom = self.bom_ids[0]
        boms, lines = bom.explode(self, 1.0)
        for line in lines:
            product = line[0].product_id
            kit.line_ids.create({
                'kit_id': kit.id,
                'product_id': product.id,
                'product_qty': line[1]['qty'] * quantity,
                'factor': line[1]['qty'],
            })
        action = self.env.ref(
            'mrp_planned_pick_kit.action_mrp_planned_pick_kit').read()[0]
        action['res_id'] = kit.id
        return action
