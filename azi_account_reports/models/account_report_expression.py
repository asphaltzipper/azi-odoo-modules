from odoo import models, fields


class AccountReportExpression(models.Model):
    _inherit = "account.report.expression"

    def init(self):
        super().init()
        receivable_due_date = self.env.ref('account_reports.aged_receivable_line_due_date', raise_if_not_found=False)
        payable_due_date = self.env.ref('account_reports.aged_payable_line_due_date', raise_if_not_found=False)
        payable_expected_date = self.env.ref('account_reports.aged_payable_line_expected_date', raise_if_not_found=False)
        receivable_expected_date = self.env.ref('account_reports.aged_receivable_line_expected_date', raise_if_not_found=False)
        if receivable_due_date:
            receivable_due_date.unlink()
        if payable_due_date:
            payable_due_date.unlink()
        payable_expected_date and payable_expected_date.unlink()
        receivable_expected_date and receivable_expected_date.unlink()
