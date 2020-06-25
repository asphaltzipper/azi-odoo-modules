# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockRequest(models.Model):
    _inherit = 'stock.request'

    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        related='product_id.product_tmpl_id',
        string='Template',
        store=True)

    note = fields.Char(string='Note')

    sale_order_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Sale Line')

    sale_partner_id = fields.Many2one(
        comodel_name='res.partner',
        related='sale_order_line_id.order_id.partner_id',
        # compute='_compute_sale_partner_id',
        string='Partner',
        store=True)

    # @api.depends('sale_order_line_id')
    # def _compute_sale_partner_id(self):
    #     for rec in self:
    #         rec.sale_partner_id = \
    #             rec.sale_order_line_id and \
    #             rec.sale_order_line_id.order_id.partner_id or False

    # TODO: enforce sale_order_line_id is unique

    # TODO: make a wizard for linking stock requests to sales order lines
    # The wizard should tie the delivery and production stock moves together
