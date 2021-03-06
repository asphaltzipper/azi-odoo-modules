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

    scheduled = fields.Boolean(
        string='Scheduled',
        required=True,
        default=False)

    sale_order_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Sale Line')

    sale_partner_id = fields.Many2one(
        comodel_name='res.partner',
        related='sale_order_line_id.order_id.partner_id',
        string='Partner',
        store=True)

    finished_goods = fields.Boolean('Finished Goods', related='product_id.categ_id.finished_goods', store=True)

    sold = fields.Boolean(
        string='Sold',
        compute='_compute_sold',
        required=True,
        default=False,
        store=True)

    production_ids = fields.Many2many(copy=False)

    @api.depends('sale_order_line_id')
    def _compute_sold(self):
        for rec in self:
            rec.sold = rec.sale_order_line_id and \
                       rec.sale_order_line_id.state != 'cancel' or False

    # TODO: enforce sale_order_line_id is unique

    # TODO: make a wizard for linking stock requests to sales order lines
    # The wizard should tie the delivery and production stock moves together
