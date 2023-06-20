from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.constrains('order_id.requisition_id', 'product_id')
    def _check_product_not_in_blanket(self):
        for record in self:
            if not record.order_id.requisition_id:
                blanket_line = self.env['purchase.requisition.line'].search([
                    ('product_id', '=', record.product_id.id),
                    ('requisition_id.state', 'not in', ('cancel', 'done')),
                    ('requisition_id.vendor_id', '=', record.order_id.partner_id.id)], limit=1)
                if blanket_line:
                    raise ValidationError('There is a blanket order %s for this product, '
                                          'please try to link the PO to this '
                                          'Blanket order' % blanket_line.requisition_id.name)
