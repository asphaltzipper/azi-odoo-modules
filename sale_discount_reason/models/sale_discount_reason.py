# -*- coding: utf-8 -*-
# Copyright 2017 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api


class SaleDiscountReason(models.Model):
    _name = "sale.discount.reason"
    _description = "Sale Line Discount Reason"

    name = fields.Char(
        string='Discount Reason')


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    discount_reason_id = fields.Many2one(
        comodel_name='sale.discount.reason',
        string='Discount Reason')

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        res.update({'discount_reason_id': self.discount_reason_id.id})
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    discount_reason_id = fields.Many2one(
        comodel_name='sale.discount.reason',
        string='Discount Reason')
