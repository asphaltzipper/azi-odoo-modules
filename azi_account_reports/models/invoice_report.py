# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    state_id = fields.Many2one(comodel_name='res.country.state', string='State')

    def _select(self):
        return super(AccountInvoiceReport, self)._select() + ", sub.state_id as state_id"

    def _sub_select(self):
        return super(AccountInvoiceReport, self)._sub_select() + ", ship_partner.state_id as state_id"

    def _from(self):
        return super(AccountInvoiceReport, self)._from() + """
                left join res_partner as ship_partner on ship_partner.id=ai.partner_shipping_id"""

    def _group_by(self):
        return super(AccountInvoiceReport, self)._group_by() + ", ship_partner.state_id"
