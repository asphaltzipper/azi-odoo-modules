from odoo import models, api


class AccountRegisterPayments(models.TransientModel):
    _inherit = "account.register.payments"

    @api.multi
    def _groupby_invoices(self):
        '''Groups the invoices linked to the wizard.

        If the group_invoices option is activated, invoices will be grouped
        according to their commercial partner, their account, their type and
        the account where the payment they expect should end up. Otherwise,
        invoices will be grouped so that each of them belongs to a
        distinct group.

        :return: a dictionary mapping, grouping invoices as a recordset under each of its keys.
        '''
        if not self.group_invoices:
            return {inv.id: inv for inv in self.invoice_ids.sorted(key=lambda i: i.partner_id.name)}

        results = {}
        # Create a dict dispatching invoices according to their commercial_partner_id, account_id, invoice_type and partner_bank_id
        for inv in self.invoice_ids.sorted(key=lambda i: i.partner_id.name):
            key = self._get_payment_group_key(inv)
            if not key in results:
                results[key] = self.env['account.invoice']
            results[key] += inv
        return results