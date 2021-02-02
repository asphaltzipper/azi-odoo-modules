# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    e_kanban = fields.Boolean(
        related='product_variant_ids.e_kanban',
        readonly=False)

    e_kanban_ids = fields.One2many(
        related='product_variant_ids.e_kanban_ids')

    e_kanban_avg_qty = fields.Float(
        related='product_variant_ids.e_kanban_avg_qty')

    e_kanban_count = fields.Integer(
        related='product_variant_ids.e_kanban_count',
        store=True)

    e_kanban_verified = fields.Boolean(
        related='product_variant_ids.e_kanban_verified',
        store=True)

    def action_kanban_cards(self):
        action = self.env.ref('stock_request_kanban.stock_request_kanban_action').read()[0]
        action['domain'] = [('product_id', 'in', self.product_variant_ids.ids)]
        return action


class ProductProduct(models.Model):
    _inherit = "product.product"

    e_kanban = fields.Boolean(
        string='E-Kanban',
        default=False,
        help="Material planning (MRP) for This product will be handled by electronic kanban")

    e_kanban_ids = fields.One2many(
        comodel_name='stock.request.kanban',
        inverse_name='product_id',
        string='Kanban Cards')

    e_kanban_avg_qty = fields.Float(
        string='Kanban Qty',
        compute='_compute_e_kanban',
        help="Default procurement quantity for electronic kanban ordering")

    e_kanban_count = fields.Integer(
        string='Kanban Count',
        compute='_compute_e_kanban',
        help="Number of bins/kanbans maintained for this product")

    e_kanban_verified = fields.Boolean(
        string='Kanban Verified',
        compute='_compute_e_kanban',
        help="The existence of the bin/kanban has been verified")

    @api.depends('e_kanban_ids')
    def _compute_e_kanban(self):
        for product in self:
            product.e_kanban_avg_qty = 0
            product.e_kanban_verified = False
            product.e_kanban_count = len(product.e_kanban_ids)
            if product.e_kanban_count:
                product.e_kanban_avg_qty = sum(product.e_kanban_ids.mapped('product_qty')) / product.e_kanban_count
                product.e_kanban_verified = True

    def action_kanban_cards(self):
        action = self.env.ref('stock_request_kanban.stock_request_kanban_action').read()[0]
        action['domain'] = [('product_id', 'in', self.ids)]
        return action
