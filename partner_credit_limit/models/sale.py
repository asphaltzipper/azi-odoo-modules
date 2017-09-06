# -*- coding: utf-8 -*-
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.

from odoo import api, models, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def check_limit(self):
        self.ensure_one()
        partner = self.partner_id

        # sum unreconciled debits and credits from journal items
        domain = [('partner_id', '=', partner.id),
                  ('account_id.user_type_id.name', 'in', ['Receivable', 'Payable']),
                  ('full_reconcile_id', '=', False)]
        move_lines = self.env['account.move.line'].search(domain)
        debit, credit = 0.0, 0.0
        today_dt = datetime.today().strftime(DF)
        for line in move_lines:
            if line.date_maturity < today_dt:
                credit += line.debit

        # sum sale order lines that are not yet invoiced, from all the sale orders that are confirmed
        domain = [('order_id', '!=', self.id),
                  ('order_id.partner_id', '=', self.partner_id.id),
                  ('invoice_status', '=', 'to invoice'),
                  ('order_id.state', 'not in', ['draft', 'cancel', 'sent'])]
        order_lines = self.env['sale.order.line'].search(domain)
        not_invoiced_amount = sum([x.price_subtotal for x in order_lines])

        # sum the total amount of all the invoices that are in draft state
        domain = [('partner_id', '=', self.partner_id.id),
                  ('state', '=', 'draft')]
        draft_invoices = self.env['account.invoice'].search(domain)
        draft_invoices_amount = sum([x.amount_total for x in draft_invoices])

        debit += line.credit

        if (credit - debit + self.amount_total) > partner.credit_limit:
            if not partner.over_credit:
                msg = 'Can not confirm Sale Order,Total mature due Amount ' \
                      '%s as on %s !\nCheck Partner Accounts or Credit ' \
                      'Limits !' % (credit - debit, today_dt)
                raise UserError(_('Credit Over Limits !\n' + msg))
            else:
                partner.write({
                    'credit_limit': credit - debit + self.amount_total})
                return True
        else:
            return True

    @api.one
    def check_limit(self):
        if self.payment_term_id != self.env.ref('account.account_payment_term_immediate'):
            if self.partner_id.warning_type != 'none':
                if self.partner_id.warning_type in ('date', 'all'):
                    d = datetime.timedelta(days=self.partner_id.credit_limit_days)
                    if self.partner_id.payment_earliest_due_date == False:
                        return True
                    data = self.partner_id.payment_earliest_due_date
                    if data + d < datetime.now():
                        msg = 'Can not confirm the order because the customer does not have enough credit. \
                            You can transition your billing policy to direct debit to be able to bill."'
                        raise Warning(_(msg))
                        return False
                if self.order_id and self.order_id.partner_id.warning_type in ('value','all'):
                    # We sum from all the sale orders that are approved, the sale order
                    # lines that are not yet invoiced
                    domain = [('order_id.partner_id', '=', self.partner_id.id),
                              ('invoice_status', '=', 'to invoice'),
                              ('order_id.state', 'not in', ['draft', 'cancel', 'sent'])]
                    order_lines = self.env['sale.order.line'].search(domain)
                    none_invoiced_amount = sum([x.price_subtotal for x in order_lines])
                    # We sum from all the invoices that are in draft the total amount
                    domain = [
                        ('partner_id', '=', self.partner_id.id), ('state', '=', 'draft')]
                    draft_invoices = self.env['account.invoice'].search(domain)
                    draft_invoices_amount = sum([x.amount_total for x in draft_invoices])

                    available_credit = self.partner_id.credit_limit - \
                        self.partner_id.credit - \
                        none_invoiced_amount - draft_invoices_amount
                    if self.amount_total > available_credit:
                        msg = 'Can not confirm the order because the customer does not have enough credit. \
                            You can transition your billing policy to direct debit to be able to bill."'
                        raise Warning(_(msg))
                        return False
        return True

    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            order.check_limit()
        return res
