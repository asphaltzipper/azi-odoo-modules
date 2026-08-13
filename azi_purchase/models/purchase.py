# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    send_date = fields.Datetime(
        string='Date Sent'
    )

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        for line in self.mapped('order_line'):
            seller = line.product_id.seller_ids.filtered(
                lambda s: s.partner_id == line.order_id.partner_id and s.product_code == line.vendor_product_code)
            if seller:
                seller = seller.sorted(key=lambda x: x.sequence)[0]
                if seller.price != line.price_unit:
                    message = "Purchase price changed from %s to %s for vendor %s" % (seller.price, line.price_unit,
                                                                                      seller.partner_id.display_name)
                    seller.price = line.price_unit
                    line.product_id.message_post(body=message)
        return res


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def _action_send_mail(self, auto_commit=False):
        if self._context.get('default_model') == 'purchase.order' and self._context.get('default_res_id'):
            if not self.filtered('subtype_id.internal'):
                order = self.env['purchase.order'].browse([self._context['default_res_id']])
                order.send_date = fields.datetime.now()
        return super(MailComposeMessage, self.with_context(mail_post_autofollow=True))._action_send_mail(auto_commit=auto_commit)

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    vendor_product_code = fields.Char(
        string="Vendor Product Code",
    )
    product_virtual_available = fields.Float(
        string='Product Forecasted Quantity',
        related='product_id.virtual_available',
        depends=['product_id'],
    )
    product_tmpl_id = fields.Many2one('product.template', related='product_id.product_tmpl_id')
    supplierinfo_id = fields.Many2one('product.supplierinfo', 'Vendor Pricelist')

    def _apply_supplierinfo(self, seller):
        if not seller:
            return
        self.vendor_product_code = seller.product_code
        self.price_unit = seller.price
        name = seller.product_name or self.product_id.name
        if seller.product_code:
            name = f"[{seller.product_code}] {name}"
        if self.product_id.description_purchase:
            name += '\n' + self.product_id.description_purchase
        self.name = name

    def _product_id_change(self):
        super(PurchaseOrderLine, self)._product_id_change()
        if not self.product_id:
            self.supplierinfo_id = False
            return
        params = {'order_id': self.order_id}
        seller = self.product_id._select_seller(
            partner_id=self.partner_id,
            quantity=self.product_qty,
            date=self.order_id.date_order and self.order_id.date_order.date(),
            uom_id=self.product_uom,
            params=params)
        self.supplierinfo_id = seller
        self._apply_supplierinfo(seller)

    @api.onchange('supplierinfo_id')
    def _onchange_supplierinfo_id(self):
        if self.supplierinfo_id:
            self._apply_supplierinfo(self.supplierinfo_id)
