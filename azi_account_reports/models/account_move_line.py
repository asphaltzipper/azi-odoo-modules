# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    product_categ_id = fields.Many2one(
        comodel_name='product.category',
        related='product_id.product_tmpl_id.categ_id',
        string='Product Category',
        store=True)
