from collections import defaultdict
from odoo import models, api, _
from odoo.exceptions import UserError
from odoo.tools import frozendict


class AccountRegisterPayments(models.TransientModel):
    _inherit = "account.payment.register"

    def _get_batches(self):
        """ Group the account.move.line linked to the wizard together.
        Lines are grouped if they share 'partner_id','account_id','currency_id' & 'partner_type' and if
        0 or 1 partner_bank_id can be determined for the group.
        :return: A list of batches, each one containing:
            * payment_values:   A dictionary of payment values.
            * moves:        An account.move recordset.
        """
        self.ensure_one()

        lines = self.line_ids._origin

        if len(lines.company_id) > 1:
            raise UserError(_("You can't create payments for entries belonging to different companies."))
        if not lines:
            raise UserError(_("You can't open the register payment wizard without at least one receivable/payable line."))

        batches = defaultdict(lambda: {'lines': self.env['account.move.line']})
        banks_per_partner = defaultdict(lambda: {'inbound': set(), 'outbound': set()})
        # Sort lines based on partner name
        for line in lines.sorted(key=lambda l: l.partner_id.name):
            batch_key = self._get_line_batch_key(line)
            vals = batches[frozendict(batch_key)]
            vals['payment_values'] = batch_key
            vals['lines'] += line
            banks_per_partner[batch_key['partner_id']]['inbound' if line.balance > 0.0 else 'outbound'].add(
                batch_key['partner_bank_id']
            )

        partner_unique_inbound = {p for p, b in banks_per_partner.items() if len(b['inbound']) == 1}
        partner_unique_outbound = {p for p, b in banks_per_partner.items() if len(b['outbound']) == 1}

        # Compute 'payment_type'.
        batch_vals = []
        seen_keys = set()
        for i, key in enumerate(list(batches)):
            if key in seen_keys:
                continue
            vals = batches[key]
            lines = vals['lines']
            merge = (
                batch_key['partner_id'] in partner_unique_inbound
                and batch_key['partner_id'] in partner_unique_outbound
            )
            if merge:
                for other_key in list(batches)[i+1:]:
                    if other_key in seen_keys:
                        continue
                    other_vals = batches[other_key]
                    if all(
                        other_vals['payment_values'][k] == v
                        for k, v in vals['payment_values'].items()
                        if k not in ('partner_bank_id', 'payment_type')
                    ):
                        # add the lines in this batch and mark as seen
                        lines += other_vals['lines']
                        seen_keys.add(other_key)
            balance = sum(lines.mapped('balance'))
            vals['payment_values']['payment_type'] = 'inbound' if balance > 0.0 else 'outbound'
            if merge:
                partner_banks = banks_per_partner[batch_key['partner_id']]
                vals['partner_bank_id'] = partner_banks[vals['payment_values']['payment_type']]
                vals['lines'] = lines
            batch_vals.append(vals)
        return batch_vals