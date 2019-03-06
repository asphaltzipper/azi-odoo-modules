# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions


class SaleOrder(models.Model):
    _inherit = "sale.order"

    bypass_warning = fields.Boolean(string='Bypass Warning')
    partner_warn = fields.Selection(related='partner_id.sale_warn')
    partner_warn_msg = fields.Text(string='Partner Warning', related='partner_id.sale_warn_msg', readonly=True)
    partner_comment = fields.Text(string='Partner Comment', related='partner_id.comment', readonly=True)
    user_id = fields.Many2one(
        domain=['|', ('active', '=', True), ('active', '=', False)])

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
        return super(SaleOrder, self).action_confirm()

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

    @api.multi
    def action_cancel(self):
        for order in self:
            if order.order_line.filtered(lambda x: x.qty_delivered):
                raise exceptions.UserError("Can't cancel orders with lines that have been delivered")
        return super(SaleOrder, self).action_cancel()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    delivery_remaining_qty = fields.Float(
        string="Remaining Qty",
        readonly=True,
        compute='_compute_delivery_remaining_qty',
        store=True)

    @api.depends('product_uom_qty', 'qty_delivered')
    def _compute_delivery_remaining_qty(self):
        for line in self:
            line.delivery_remaining_qty = line.product_uom_qty - line.qty_delivered
