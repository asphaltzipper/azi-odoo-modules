import time

from openerp import api, fields, models, _
from openerp.tools.float_utils import float_is_zero, float_compare

class RequestRelease(models.TransientModel):
    _name = "request.release"
    _description = "Request Release"

    product_ids = fields.One2many('request.release.item', 'request_id', string='Product', domain=[('product_id', '!=', False)])

    @api.model
    def default_get(self, fields):
        res = super(RequestRelease, self).default_get(fields)
        po_id = self.env.context.get('active_id')
        p_order = self.env['purchase.order'].browse(po_id)
        items = []
        packs = []
        for op in p_order.order_line:
            item = {
                'product_id': op.product_id.id,
                'product_uom_id': op.product_uom.id,
                'product_qty': op.product_qty,
                'destinationloc_id': p_order._get_destination_location(),
                'sourceloc_id': p_order.partner_id.property_stock_supplier.id,
                'request_date': op.date_planned
            }
            if op.product_id:
                items.append([0, 0, item])
        res.update(product_ids=items)
        return res

    @api.multi
    def do_picking_create(self):
        lines = []
        picking_obj = self.env['stock.picking']
        po_id = self.env.context.get('active_id')
        p_order = self.env['purchase.order'].browse(po_id)
        for item_line in self.product_ids:
            lines.append([0, 0, {
                    'origin': p_order.name,
                    'name': item_line.product_id.name,
                    'product_id': item_line.product_id.id,
                     'product_uom_qty': item_line.product_qty,
                     'product_uom': item_line.product_uom_id.id,
            }])
        if not p_order.group_id:
            p_order.group_id = p_order.group_id.create({
                'name': p_order.name,
                'partner_id': p_order.partner_id.id
            })
        picking_id = picking_obj.create({'partner_id': p_order.partner_id.id,
                            'origin': p_order.name,
                            'min_date': item_line.request_date,
                            'picking_type_id': p_order.picking_type_id.id,
                            'location_id': p_order.partner_id.property_stock_supplier.id,
                            'location_dest_id': p_order._get_destination_location(),
                            'move_lines': lines,
                                         })
        for data in picking_id.move_lines:
            move_ids = data.action_confirm()
            moves = self.env['stock.move'].browse(move_ids)
            moves.force_assign()
        if picking_id:
            picking_id.write({'group_id': p_order.group_id.id})
            if p_order.blanket:
                count = p_order.blanket_count + 1
                p_order.write({'blanket_count': count})
        return True

class RequestReleaseItem(models.TransientModel):
    _name = "request.release.item"
    _description = "Request Release Items"

    product_id = fields.Many2one('product.product', 'Product')
    product_qty = fields.Float(string='Quantity')
    product_uom_id = fields.Many2one('product.uom', 'Product Unit of Measure')
    request_id = fields.Many2one('request.release', 'Request ID')
    sourceloc_id = fields.Many2one('stock.location', 'Source Location', required=True)
    destinationloc_id = fields.Many2one('stock.location', 'Destination Location', required=True)
    request_date = fields.Datetime(string='Date')

