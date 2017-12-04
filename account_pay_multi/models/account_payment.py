# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.account.models.account_payment import MAP_INVOICE_TYPE_PAYMENT_SIGN
from odoo.addons.account.models.account_payment import MAP_INVOICE_TYPE_PARTNER_TYPE


class account_register_payments(models.TransientModel):
    _inherit = "account.register.payments"

    multiple_supplier = fields.Boolean('Multiple Vendors')
    partner_ids = fields.Many2many('res.partner', 'partner_payment_rel', 'partner_id', 'payment_id', 'Partner')

    @api.model
    def default_get(self, fields):
        '''
        default_get(fields) -> default_values

        Return default values for the fields in ``fields_list``. Default
        values are determined by the context, user defaults, and the model
        itself.

        :param fields_list: a list of field names
        :return: a dictionary mapping each field name to its corresponding
            default value, if it has one.

        This method is overwritten(calling directly ORM method to eliminate validation for multiple vendor)
        '''
        rec = models.Model.default_get(self, fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        multiple_supplier = False
        # Checks on context parameters
        if not active_model or not active_ids:
            raise UserError(
                _("Programmation error: wizard action executed without active_model or active_ids in context."))
        if active_model != 'account.invoice':
            raise UserError(_(
                "Programmation error: the expected model for this action is 'account.invoice'. The provided one is '%d'.") % active_model)

        # Checks on received invoice records
        invoices = self.env[active_model].browse(active_ids)
        if any(invoice.state != 'open' for invoice in invoices):
            raise UserError(_("You can only register payments for open invoices"))
        if any(inv.commercial_partner_id != invoices[0].commercial_partner_id for inv in invoices):
            multiple_supplier = True
        if any(MAP_INVOICE_TYPE_PARTNER_TYPE[inv.type] != MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type] for inv in
               invoices):
            raise UserError(_("You cannot mix customer invoices and vendor bills in a single payment."))
        if any(inv.currency_id != invoices[0].currency_id for inv in invoices):
            raise UserError(_("In order to pay multiple invoices at once, they must use the same currency."))

        total_amount = sum(inv.residual * MAP_INVOICE_TYPE_PAYMENT_SIGN[inv.type] for inv in invoices)
        communication = ' '.join([ref for ref in invoices.mapped('reference') if ref])
        partner_ids = []
        for invoice in invoices:
            if invoice.commercial_partner_id.id not in partner_ids:
                partner_ids.append(invoice.commercial_partner_id.id)
        rec.update({
            'amount': abs(total_amount),
            'currency_id': invoices[0].currency_id.id,
            'payment_type': total_amount > 0 and 'inbound' or 'outbound',
            'partner_ids': [(6, 0, partner_ids)],
            'partner_id': invoices[0].commercial_partner_id.id,
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
            'communication': communication,
            'multiple_supplier': multiple_supplier
        })
        return rec

    def _get_invoices_multi_vendor(self, partner):
        '''
        Args:
            partner: partner_id for which payment is going to be made

        Returns: list of browse record of invoices, amount for those invoices

        '''
        invoice_ids = self.env['account.invoice'].browse(self._context.get('active_ids'))
        filtered_invoices = []
        total_amount = 0.0
        for invoice in invoice_ids:
            if invoice.commercial_partner_id.id == partner:
                filtered_invoices.append(invoice)
                total_amount += invoice.amount_total
        return filtered_invoices, total_amount

    def get_payment_vals_multi_vendor(self, partner):
        '''

        Args:
            partner: partner_id for which payment is going to be made

        Returns: set of dictionary of key and value of account payment fields

        '''
        res = super(account_register_payments, self).get_payment_vals()
        invoice_ids, total_amount = self._get_invoices_multi_vendor(partner)
        res.update({'partner_id': partner,
                    'invoice_ids': [(4, inv.id, None) for inv in invoice_ids],
                    'amount': total_amount})
        return res

    @api.multi
    def create_payment(self):
        '''
        this is an object method
        if single supplier, super method is called to create method,
        else: payment is created group by partner
        '''
        if not self.multiple_supplier:
            return super(account_register_payments, self).create_payment()
        for partner in self.partner_ids:
            context = dict(self._context)
            payment = self.env['account.payment'].with_context(context).create(
                self.get_payment_vals_multi_vendor(partner.id))
            payment.post()
        return {'type': 'ir.actions.act_window_close'}
