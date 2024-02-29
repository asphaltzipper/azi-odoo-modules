from odoo import api, models, fields, _


class StockRequestAbstract(models.AbstractModel):
    _inherit = 'stock.request.abstract'

    product_deprecated = fields.Boolean(
        related='product_id.deprecated',
        string='Obsolete',
        readonly=True,
        store=True)

    product_active = fields.Boolean(
        related='product_id.active',
        string='Product Active',
        readonly=True,
        store=True)

    product_responsible_id = fields.Many2one(
        related='product_id.responsible_id',
        readonly=True,
        store=True)

    product_type = fields.Selection(
        related='product_id.type',
        readonly=True,
        store=True)


class StockRequest(models.Model):
    _inherit = 'stock.request'

    def action_confirm(self):
        res = super(StockRequest, self).action_confirm()
        for record in self:
            if record.kanban_id and record.product_id.type == 'product':
                available_qty = record.product_id.qty_available
                other_kanbans = record.product_id.e_kanban_ids.filtered(lambda x: x.id != record.kanban_id.id)
                probable_qty = other_kanbans and sum(other_kanbans.mapped('product_uom_qty')) or 0
                if 0 <= available_qty <= probable_qty:
                    # available_qty may be more accurate than probable_qty when:
                    # - kanban scanned for a newly created product
                    # - kanban scanned after some additional product has already been consumed
                    continue
                location_id = record.kanban_id.location_id.id
                if probable_qty > 0:
                    stock_inventory = self.env['stock.inventory'].create({
                        'name': 'kanban order - %s' % record.product_id.name,
                        'product_selection': 'one',
                        'product_ids': [[6, False, [record.product_id.id]]],
                        'location_ids': [[6, False, [location_id]]]})

                    stock_inventory.action_state_to_in_progress()
                    stock_inventory.mapped("stock_quant_ids")[0].inventory_quantity = probable_qty
                    stock_inventory.mapped("stock_quant_ids")[0].action_apply_inventory()
                    stock_inventory.action_state_to_done()
        return res


class StockRequestOrder(models.Model):
    _inherit = 'stock.request.order'

    request_ids = fields.Many2many('stock.request', string='Stock Requests')
