# -*- coding: utf-8 -*-

from odoo import models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _get_move_vals(self, journal=None):
        """ Return dict to create the payment move
        """
        res = super(AccountPayment, self)._get_move_vals(journal)
        if self.check_number:
            res['ref'] = "CHECK %d: %s" % (self.check_number, res['ref'])
        return res
