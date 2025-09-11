# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions


class SaleOrder(models.Model):
    _inherit = "sale.order"

    credit_app_date = fields.Date(
        related='partner_id.credit_app_date',
        readonly=True)
    credit_warn = fields.Boolean('Credit Application Warning', related='partner_id.credit_warn', store=True)
    bypass_credit_warn = fields.Boolean('Bypass Credit Warning')

    @api.onchange('credit_warn')
    def _onchange_credit_warn(self):
        if self.credit_warn:
            return {'warning': {
                'title': 'Credit Application Warning',
                'message': self.partner_id.credit_warn_msg,
            }}

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            if not self.env['res.partner.credit'].search([('partner_id', '=', order.partner_id.id),
                                                          ('state', '=', 'draft')]) and order.bypass_credit_warn:
                self.env['res.partner.credit'].create({'partner_id': order.partner_id.id, 'order_id': order.id})
        return res
