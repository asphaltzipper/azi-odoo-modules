from odoo import api, models, fields, _


class StockRequest(models.AbstractModel):
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

    @api.multi
    def action_confirm(self):
        res = super(StockRequest, self).action_confirm()
        for record in self:
            if record.kanban_id:
                kanban_qty = record.product_id.e_kanban_avg_qty
                qty_available = record.product_id.qty_available
                real_quantity = kanban_qty - qty_available
                location_id = record.kanban_id.location_id.id
                if real_quantity:
                    stock_inventory = self.env['stock.inventory'].create({'name': '%s - adjustment' % record.product_id.name,
                                                                          'filter': 'product',
                                                                          'product_id': record.product_id.id,
                                                                          'location_id': location_id})
                    stock_inventory.action_start()
                    stock_inventory.write({'line_ids': [(0, _, {'product_id': record.product_id.id,
                                                                'product_qty': real_quantity,
                                                                'location_id': location_id})]})
                    stock_inventory.action_validate()
        return res


class StockRequestOrder(models.Model):
    _inherit = 'stock.request.order'

    request_ids = fields.Many2many('stock.request', string='Stock Requests')
