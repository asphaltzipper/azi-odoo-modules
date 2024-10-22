# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import formatLang


class AccountTax(models.Model):
    _inherit = 'account.tax'

    retail_tax = fields.Boolean('Retail Taxes')


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _default_retail_tax(self):
        return self.env['account.tax'].search([('retail_tax', '=', True)], limit=1)

    retail_account_tax_id = fields.Many2one('account.tax', string='Retail Taxes', ondelete='restrict',
                                            default=_default_retail_tax)
    retail_delivery_fees = fields.Monetary(
        string="Retail Delivery Fees",
        compute='_compute_tax_totals',
        compute_sudo=False,
        store=True,
    )
    tax_totals_report = fields.Binary("Tax Total Report", compute='_compute_tax_totals_report')

    @api.depends('line_ids', 'retail_delivery_fees', 'retail_account_tax_id')
    def _compute_tax_totals_report(self):
        for move in self:
            retail_taxes = self.env['account.tax'].search([('retail_tax', '=', True)]).mapped('id')
            taxes = {'group_taxes': []}
            total_tax_without_retail = sum([line._convert_to_tax_line_dict().get('tax_amount') for line in move.line_ids.filtered(
                lambda line: line.display_type == 'tax' and line.tax_line_id.id not in retail_taxes)])
            taxes.update(group_taxes=[
                {'tax_amount': formatLang(self.env, total_tax_without_retail, currency_obj=move.currency_id),
                 'tax_label': 'Total Tax'},
                {'tax_amount': formatLang(self.env, move.retail_delivery_fees, currency_obj=move.currency_id),
                 'tax_label': 'Retail Delivery Fees'}])
            move.tax_totals_report = taxes

    @api.depends_context('lang')
    @api.depends(
        'invoice_line_ids.currency_rate',
        'invoice_line_ids.tax_base_amount',
        'invoice_line_ids.tax_line_id',
        'invoice_line_ids.price_total',
        'invoice_line_ids.price_subtotal',
        'invoice_payment_term_id',
        'partner_id',
        'currency_id',
        'retail_account_tax_id'
    )
    def _compute_tax_totals(self):
        """ Computed field used for custom widget's rendering.
            Only set on invoices.
        """
        for move in self:
            if move.is_invoice(include_receipts=True):
                # Create a line for retail tax
                apply_taxes = self.env['ir.config_parameter'].get_param('azi_account.apply_retail_taxes')
                if apply_taxes and move.retail_account_tax_id and move.partner_id.state_id.code == 'CO' and move.move_type in (
                        'out_invoice', 'in_invoice'):
                    retail_taxes = self.env['account.tax'].search([('retail_tax', '=', True)]).mapped('id')
                    taxes = move.id and move.invoice_line_ids.mapped('tax_ids') or move.invoice_line_ids.mapped('tax_ids')._origin
                    retail_tax_applied = taxes.filtered(lambda tax: tax.id in retail_taxes)
                    if not retail_tax_applied:
                        move.invoice_line_ids += self.env['account.move.line'].new({
                            'partner_id': move.partner_id.id,
                            'currency_id': move.currency_id.id,
                            'tax_ids': [move.retail_account_tax_id.id],
                        })
                    if retail_tax_applied:
                        retail_fee = sum(move.line_ids.filtered(
                            lambda l: set(l.tax_line_id.mapped('id')) & set(retail_taxes)).mapped('credit'))
                        move.retail_delivery_fees = retail_fee
        super(AccountMove, self)._compute_tax_totals()

    @api.constrains('invoice_line_ids')
    def _check_retail_taxes(self):
        apply_taxes = self.env['ir.config_parameter'].sudo().get_param('azi_account.apply_retail_taxes')
        if apply_taxes and self.retail_account_tax_id and self.partner_id.state_id.code == 'CO' and self.move_type in (
                'out_invoice', 'in_invoice'):
            retail_taxes = set(self.env['account.tax'].search([('retail_tax', '=', True)]).mapped('id'))
            retail_lines = self.invoice_line_ids.filtered(
                lambda line: set(line.tax_ids.mapped('id')) & retail_taxes)
            if len(retail_lines) > 1:
                raise ValidationError(_('You should have only one retail tax applied per invoice'))
