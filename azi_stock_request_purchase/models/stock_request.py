from odoo import models, api, fields


class StockRequest(models.Model):
    _inherit = 'stock.request'

    is_purchase = fields.Boolean('Is Purchase?', compute='_compute_is_purchase_or_manufacture')
    can_edit_procure = fields.Boolean('Edit Procure', compute='_compute_edit_procure')
    to_procure = fields.Boolean('Procure')
    vendor_id = fields.Many2one('res.partner', 'Vendor', compute='_compute_vendor')
    stock_type = fields.Char('Purchase or Manufacture', compute='_compute_is_purchase_or_manufacture')
    purchase_qty_in_progress = fields.Float(compute='_compute_purchase_qty')
    purchase_name = fields.Char(compute='_compute_purchase_name')

    @api.depends('purchase_ids')
    def _compute_vendor(self):
        for record in self:
            purchase = record.purchase_ids.filtered(lambda p: p.state != 'cancel')
            record.vendor_id = purchase and purchase.partner_id or None

    @api.depends('route_ids')
    def _compute_is_purchase_or_manufacture(self):
        for record in self:
            is_purchase = record.route_ids.mapped('rule_ids').filtered(lambda r: r.action == 'buy')
            is_manufacturing = record.route_ids.mapped('rule_ids').filtered(lambda r: r.action == 'manufacture')
            record.is_purchase = is_purchase and True or False
            record.stock_type = is_purchase and 'Purchase' or (is_manufacturing and 'Manufacture' or '')

    @api.depends('is_purchase')
    def _compute_edit_procure(self):
        for record in self:
            if record.is_purchase:
                record.can_edit_procure = (
                        not record.purchase_ids or
                        all(p.state == 'cancel' for p in record.purchase_ids)
                )
            else:
                record.can_edit_procure = False

    @api.depends('purchase_line_ids')
    def _compute_purchase_qty(self):
        for record in self:
            product_qty = record.purchase_line_ids.filtered(lambda l: l.state != 'cancel' and l.qty_received == 0).mapped('product_qty')
            record.purchase_qty_in_progress = product_qty and sum(product_qty) or 0

    @api.depends('purchase_ids')
    def _compute_purchase_name(self):
        for record in self:
            record.purchase_name = record.purchase_ids and record.purchase_ids[0].display_name or ''
