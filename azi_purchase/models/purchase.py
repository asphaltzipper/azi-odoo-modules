# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    send_date = fields.Datetime(
        string='Date Sent'
    )


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail(self, auto_commit=False):
        if self._context.get('default_model') == 'purchase.order' and self._context.get('default_res_id'):
            if not self.filtered('subtype_id.internal'):
                order = self.env['purchase.order'].browse([self._context['default_res_id']])
                order.send_date = fields.datetime.now()
        return super(MailComposeMessage, self.with_context(mail_post_autofollow=True)).send_mail(auto_commit=auto_commit)
