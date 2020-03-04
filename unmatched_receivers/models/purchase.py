# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    show_product_received = fields.Boolean(compute='_compute_show_product_received', store=True)
    account_move_ids = fields.Many2many('account.move', compute='_compute_move_ids')

    @api.depends('qty_invoiced', 'qty_received')
    def _compute_show_product_received(self):
        for record in self:
            if record.qty_received > record.qty_invoiced:
                record.show_product_received = True
            else:
                record.show_product_received = False

    def _compute_move_ids(self):
        for record in self:
            moves = record.invoice_lines.mapped('invoice_id.move_id')
            record.account_move_ids = moves
