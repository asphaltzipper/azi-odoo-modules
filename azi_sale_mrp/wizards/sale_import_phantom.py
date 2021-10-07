from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class SaleImportPhantom(models.TransientModel):
    _name = 'sale.import.phantom'

    bom_id = fields.Many2one('mrp.bom', 'BOM', domain=[('type', '=', 'phantom')])
    quantity = fields.Integer('Parent Quantity', default=1)
    discount_reason_id = fields.Many2one('sale.discount.reason', 'Discount Reason')

    @api.constrains('quantity')
    def _check_quantity(self):
        if self.quantity <= 0:
            raise ValidationError(_('Quantity should be greater than zero'))

    def create_phantom_childs(self, child_line_ids, so_id):
        for child in child_line_ids:
            if child.child_bom_id.type == 'phantom':
                self.create_phantom_childs(child.child_line_ids, so_id)
            else:
                self.env['sale.order.line'].create({'order_id': so_id, 'product_id': child.product_id.id,
                                                    'product_uom_qty': child.product_qty * self.quantity,
                                                    'discount_reason_id': self.discount_reason_id.id})

    def import_phantom_lines(self):
        so_id = self._context.get('active_id', False)
        if so_id:
            for bom_line in self.bom_id.bom_line_ids:
                if bom_line.child_bom_id.type == 'phantom':
                    self.create_phantom_childs(bom_line.child_line_ids, so_id)
                else:
                    self.env['sale.order.line'].create({'order_id': so_id, 'product_id': bom_line.product_id.id,
                                                        'product_uom_qty': bom_line.product_qty * self.quantity,
                                                        'discount_reason_id': self.discount_reason_id.id})
