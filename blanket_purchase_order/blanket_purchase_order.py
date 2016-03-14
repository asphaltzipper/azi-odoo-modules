from datetime import datetime, timedelta
from openerp import api, fields, models, _

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    blanket = fields.Boolean(string='Blanket')
    blanket_count = fields.Integer(string="Count")

    @api.multi
    def button_approve(self):
        if self.blanket == True:
            self.write({'state': 'purchase'})
        else:
            self.write({'state': 'purchase'})
            self._create_picking()

    @api.multi
    def action_view_picking_request(self):
        '''
        This function returns an action that display existing picking orders of given purchase order ids.
        When only one found, show the picking immediately.
        '''
        action = self.env.ref('stock.action_picking_tree')
        result = action.read()[0]
        pick_obj = self.env['stock.picking']
        pick_ids = []
        result['context'] = {}
        pickings = pick_obj.search([('origin', '=', self.name)])
        for data in pickings:
            pick_ids.append(data.id)
        if len(pick_ids) > 1:
            result['domain'] = "[('id','in',[" + ','.join(map(str, pick_ids)) + "])]"
        elif len(pick_ids) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = pick_ids and pick_ids[0] or False
        return result

    @api.one
    def copy(self, default=None):
        default.update(blanket_count=0,picking_count=0)
        return super(PurchaseOrder, self).copy(default)

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    @api.v8
    def do_transfer(self):
        res = super(stock_picking, self).do_transfer()
        data = []
        purchase_obj = self.env['purchase.order']
        picking = self.browse(self._ids)
        for move in self.browse(self._ids).move_lines:
            for po_id in purchase_obj.search([('name', '=', picking.origin)]).order_line:
                if po_id.product_id.id == move.product_id.id:
                    po_id.write({'qty_received': po_id.qty_received + move.product_uom_qty})
        return True


