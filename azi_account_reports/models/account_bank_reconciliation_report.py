# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class account_bank_reconciliation_report(models.AbstractModel):
    _inherit = 'account.bank.reconciliation.report'

    def add_bank_statement_line(self, line, amount):
        report_line = super(account_bank_reconciliation_report, self).add_bank_statement_line(line, amount)
        ref = report_line['columns'][2]
        if len(ref) > 32 and not self.env.context.get('no_format'):
            report_line['columns'][2] = ref[:32] + '...'
        return report_line
