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

    e_kanban_required = fields.Integer(
        related='product_variant_ids.e_kanban_required',
        readonly=False,
    )

    e_kanban_actual = fields.Integer(
        related='product_variant_ids.e_kanban_actual',
        readonly=True,
    )

    e_kanban_verified = fields.Boolean(
        related='product_variant_ids.e_kanban_verified',
        readonly=True,
    )

    def action_kanban_cards(self):
        action = self.env.ref('stock_request_kanban.stock_request_kanban_action').read()[0]
        action['domain'] = [('product_id', 'in', self.product_variant_ids.ids)]
        if len(self) == 1:
            action['context'] = {'default_product_id':self.product_variant_ids[0].id}
        return action


class ProductProduct(models.Model):
    _inherit = "product.product"

    e_kanban = fields.Boolean(
        string='E-Kanban',
        default=False,
        help="Material planning (MRP) for This product will be handled by electronic kanban",
    )

    e_kanban_ids = fields.One2many(
        comodel_name='stock.request.kanban',
        inverse_name='product_id',
        string='Kanban Cards',
    )

    e_kanban_avg_qty = fields.Float(
        string='Kanban Qty',
        compute='_compute_e_kanban_qty',
        readonly=True,
        help="Default procurement quantity for electronic kanban ordering",
    )

    e_kanban_required = fields.Integer(
        string='Required Kanbans',
        help="Number of bins/kanbans required for this product",
    )

    e_kanban_actual = fields.Integer(
        string='Actual Kanbans',
        compute='_compute_e_kanban_qty',
        readonly=True,
        store=True,
        help="Number of bins/kanbans maintained for this product",
    )

    e_kanban_verified = fields.Boolean(
        string='Kanban Verified',
        compute='_compute_e_kanban_verified',
        readonly=True,
        search='_search_e_kanban_verified',
        help="The existence of the bin/kanban has been verified",
    )

    @api.depends('e_kanban_ids')
    def _compute_e_kanban_qty(self):
        for product in self:
            product.e_kanban_actual = len(product.e_kanban_ids)
            product.e_kanban_avg_qty = 0
            if product.e_kanban_actual:
                product.e_kanban_avg_qty = sum(product.e_kanban_ids.mapped('product_qty')) / product.e_kanban_actual

    @api.depends('e_kanban_ids', 'e_kanban_required')
    def _compute_e_kanban_verified(self):
        for product in self:
            product.e_kanban_verified = False
            if product.e_kanban_actual:
                if product.e_kanban_actual == product.e_kanban_required and \
                        all(product.e_kanban_ids.mapped('verify_date')):
                    product.e_kanban_verified = True

    @api.multi
    def _search_e_kanban_verified(self, operator, value):
        # enable search by computed field
        if operator == '!=':
            recs = self.search([]).filtered(lambda x: x.e_kanban_verified != value)
        elif operator == '=':
            recs = self.search([]).filtered(lambda x: x.e_kanban_verified == value)
        else:
            raise NotImplementedError()
        if recs:
            return[('id', 'in', [x.id for x in recs])]

    def action_kanban_cards(self):
        action = self.env.ref('stock_request_kanban.stock_request_kanban_action').read()[0]
        action['domain'] = [('product_id', 'in', self.ids)]
        if len(self) == 1:
            action['context'] = {'default_product_id': self.id}
        return action
