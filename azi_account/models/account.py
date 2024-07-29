# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    receipt_status = fields.Selection(
        selection=[
            ('yes', 'Yes'),
            ('no', 'No'),
            ('na', 'N/A')],
        string='Receipt on File',
        default='no',
        required=True,
        help="For manual handling of paper receipts on employee purchases. "
             "Check this box when a receipt is on file.")
