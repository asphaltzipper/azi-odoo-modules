# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    e_kanban = fields.Boolean(
        related='product_variant_ids.e_kanban')

    default_proc_qty = fields.Float(
        related='product_variant_ids.default_proc_qty')

    e_kanban_verified = fields.Boolean(
        related='product_variant_ids.e_kanban_verified')

    e_kanban_count = fields.Integer(
        related='product_variant_ids.e_kanban_count')


class ProductProduct(models.Model):
    _inherit = "product.product"

    e_kanban = fields.Boolean(
        string='E-Kanban',
        default=False,
        help="Material planning (MRP) for This product will be handled by electronic kanban")

    default_proc_qty = fields.Float(
        string='Kanban Qty',
        help="Default procurement quantity for electronic kanban ordering")

    e_kanban_verified = fields.Boolean(
        string='Kanban Verified',
        help="The existence of the bin/kanban has been verified")

    e_kanban_count = fields.Integer(
        string='Kanban Count',
        default=2,
        help="Number of bins/kanbans maintained for this product")
