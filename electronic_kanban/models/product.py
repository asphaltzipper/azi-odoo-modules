# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    e_kanban = fields.Boolean(
        related='product_variant_ids.e_kanban')

    default_proc_qty = fields.Float(
        related='product_variant_ids.default_proc_qty')

class ProductProduct(models.Model):
    _inherit = "product.product"

    e_kanban = fields.Boolean(
        string='E-Kanban',
        default=False,
        help="Material planning (MRP) for This product will be handled by electronic kanban")

    default_proc_qty = fields.Float(
        string='Kanban Qty',
        help="Default procurement quantity for electronic kanban ordering")

