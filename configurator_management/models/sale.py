# -*- coding: utf-8 -*-

from odoo import models, fields


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # remove the pledra domain and put it back to the default odoo domain
    # product_id = fields.Many2one(domain=[('config_ok', '=', False)])

    # we prefer to be able to select the variant if it already exists
    # rather than configuring every time
    product_id = fields.Many2one(domain=[('sale_ok', '=', True)])
