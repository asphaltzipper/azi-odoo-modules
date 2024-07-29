from odoo import models, api


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def action_post(self):
        super(AccountPayment, self).action_post()
        payment_method_check = self.env.ref('account_check_printing.account_payment_method_check')
        for payment in self.filtered(
                lambda p: p.payment_method_id == payment_method_check and p.check_manual_sequencing):
            for entry in payment.move_id:
                if entry.ref and not entry.ref.startswith("CHECK "):
                    entry.ref = "CHECK %s: %s" % (str(payment.check_number), entry.ref)
