# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


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
                raise UserError("%s:\n%s" % (title, partner.sale_warn_msg))

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
                raise UserError("Can't cancel orders with lines that have been delivered")
        return super(SaleOrder, self).action_cancel()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    delivery_remaining_qty = fields.Float(
        string="Remaining Qty",
        readonly=True,
        compute='_compute_delivery_remaining_qty',
        store=True)
    qty_available_not_res = fields.Float(
        related='product_id.qty_available_not_res',
        store=False,
    )

    @api.depends('product_uom_qty', 'qty_delivered')
    def _compute_delivery_remaining_qty(self):
        for line in self:
            line.delivery_remaining_qty = line.product_uom_qty - line.qty_delivered

    @api.onchange('product_id')
    def _onchange_product(self):
        if self.product_id:
            if self.env['mrp.bom'].sudo().search_count([('product_id', '=', self.product_id.id),
                                                        ('type', '=', 'phantom')]):
                return {'warning': {'title': _('Warning'),
                                    'message': _('You can not choose %s because it has a '
                                                 'phantom BOM') % self.product_id.display_name}}

    @api.constrains('product_id')
    def _check_product_is_phantom(self):
        for record in self:
            if self.env['mrp.bom'].sudo().search_count([('product_id', '=', record.product_id.id),
                                                        ('type', '=', 'phantom')]):
                raise ValidationError(_('You can not choose %s because it has a '
                                        'phantom BOM') % record.product_id.display_name)

    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        res = super(SaleOrderLine, self)._onchange_product_id_check_availability()
        if res.get('warning'):
            res['warning']['message'] += f"\n\nThere are {self.qty_available_not_res} " \
                                         f"{self.product_id.uom_id.name} of unreserved product available\n"
        return res
