# -*- coding: utf-8 -*-
# Copyright 2017 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api


class SaleDiscountReason(models.Model):
    _name = "sale.discount.reason"

    name = fields.Char(
        string='Discount Reason')


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    discount_reason_id = fields.Many2one(
        comodel_name='sale.discount.reason',
        string='Discount Reason')

    @api.multi
    def _prepare_invoice_line(self, qty):
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        res.update({'discount_reason_id': self.discount_reason_id.id})
        return res


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    discount_reason_id = fields.Many2one(
        comodel_name='sale.discount.reason',
        string='Discount Reason')
