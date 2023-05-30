# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountInvoice(models.Model):
    _inherit = "account.move"

    credit_app_date = fields.Date(
        related='partner_id.credit_app_date',
        readonly=True)
