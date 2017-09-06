# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions


class SaleOrder(models.Model):

    _inherit = "sale.order"

    bypass_warning = fields.Boolean(string='Bypass Warning')
    partner_warn = fields.Selection(related='partner_id.sale_warn')
    partner_warn_msg = fields.Text(string='Partner Warning', related='partner_id.sale_warn_msg', readonly=True)

    def confirm_warning(self):
        partner = self.partner_id

        # If partner has no warning, check its company
        if partner.sale_warn == 'no-message' and partner.parent_id:
            partner = partner.parent_id

        if partner.sale_warn != 'no-message':
            # Block if partner only has warning but parent company is blocked
            if partner.sale_warn != 'block' and partner.parent_id and partner.parent_id.sale_warn == 'block':
                partner = partner.parent_id
                title = ("BLOCKING for %s") % partner.name
            else:
                title = ("WARNING for %s") % partner.name
            if partner.sale_warn == 'block' or not self.bypass_warning:
                raise exceptions.UserError("%s:\n%s" % (title, partner.sale_warn_msg))

    @api.multi
    def action_confirm(self):
        for order in self:
            order.confirm_warning()
        return self.super(SaleOrder, self).action_confirm()

    @api.onchange('partner_id')
    def onchange_partner_id_warning(self):
        if not self.partner_id:
            return
        partner = self.partner_id
        # If partner has no warning, check its company
        if partner.sale_warn == 'no-message' and partner.parent_id:
            partner = partner.parent_id
        if partner.sale_warn != 'no-message':
            if partner.sale_warn == 'block':
                title = "Blocking for %s" % partner.name
            else:
                title = "Warning for %s" % partner.name
            return {'warning': {
                'title': title,
                'message': partner.sale_warn_msg,
            }}
