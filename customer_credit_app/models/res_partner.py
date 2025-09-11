# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    credit_app_date = fields.Date(
        string='Credit App Date')
    credit_warn = fields.Boolean('Credit Application Warning')
    credit_warn_msg = fields.Text('Credit Application Warning Message')


class PartnerCredit(models.Model):
    _name = 'res.partner.credit'
    _rec_name = 'partner_id'
    _description = 'Credit Application'

    requested_date = fields.Date('Requested Date', default=fields.Date.today)
    partner_id = fields.Many2one('res.partner', 'Customer')
    order_id = fields.Many2one('sale.order', 'Sales Order')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'), ('cancel', 'Cancelled')],
                             'Status', default='draft')

    def action_confirm(self):
        for record in self:
            record.partner_id.credit_warn = False
            record.state = 'confirm'

    def action_cancel(self):
        for record in self:
            record.state = 'cancel'
