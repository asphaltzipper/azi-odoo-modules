# -*- coding: utf-8 -*-

from odoo import fields, models


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    # require product variant on every bom
    # isn't there a way to do this without overriding the entire definition?
    # product_id = fields.Many2one(required=True)
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product Variant',
        required=True,
        domain="['&', ('product_tmpl_id', '=', product_tmpl_id), ('type', 'in', ['product', 'consu'])]",
        help="If a product variant is defined the BOM is available only for this product.")

    # null sorts last??!!
    # the default is null??!!!
    # I thought integer fields could not be null?
    # okay, make the default one
    sequence = fields.Integer(default=1)
