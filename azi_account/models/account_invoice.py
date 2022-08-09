# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountTax(models.Model):
    _inherit = 'account.tax'

    retail_tax = fields.Boolean('Retail Taxes')


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _default_retail_tax(self):
        return self.env['account.tax'].search([('retail_tax', '=', True)], limit=1)

    retail_account_tax_id = fields.Many2one('account.tax', string='Retail Taxes', ondelete='restrict',
                                            default=_default_retail_tax)
    retail_delivery_fees = fields.Monetary('Retail Delivery Fees', compute='_compute_amount', store=True)

    @api.onchange('invoice_line_ids', 'retail_account_tax_id')
    def _onchange_invoice_line_ids(self):
        taxes_grouped = self.get_taxes_values()
        tax_lines = self.tax_line_ids.filtered('manual')
        for tax in taxes_grouped.values():
            tax_lines += tax_lines.new(tax)
        if self.retail_account_tax_id:
            account_id = self.type in ('out_invoice', 'in_invoice') and self.retail_account_tax_id.account_id.id or \
                         self.retail_account_tax_id.refund_account_id.id
            amount = self.retail_account_tax_id._compute_amount(self.amount_untaxed, self.amount_untaxed)
            tax_lines += tax_lines.new({'invoice_id': self.id, 'name': self.retail_account_tax_id.name,
                                        'tax_id': self.retail_account_tax_id.id, 'amount': amount,
                                        'account_id': account_id})
        self.tax_line_ids = tax_lines
        return

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'tax_line_ids.amount_rounding',
                 'currency_id', 'company_id', 'date_invoice', 'type', 'date', 'retail_account_tax_id')
    def _compute_amount(self):
        round_curr = self.currency_id.round
        self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
        if self.retail_account_tax_id:
            self.retail_delivery_fees = sum(round_curr(line.amount_total) for line in self.tax_line_ids if line.tax_id.retail_tax)
        self.amount_tax = sum(round_curr(line.amount_total) for line in self.tax_line_ids if not line.tax_id.retail_tax)
        self.amount_total = self.amount_untaxed + self.amount_tax + self.retail_delivery_fees
        amount_total_company_signed = self.amount_total
        amount_untaxed_signed = self.amount_untaxed
        if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
            currency_id = self.currency_id
            rate_date = self._get_currency_rate_date() or fields.Date.today()
            amount_total_company_signed = currency_id._convert(self.amount_total, self.company_id.currency_id,
                                                               self.company_id, rate_date)
            amount_untaxed_signed = currency_id._convert(self.amount_untaxed, self.company_id.currency_id,
                                                         self.company_id, rate_date)
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign
