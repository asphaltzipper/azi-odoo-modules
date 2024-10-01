# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockQuant(models.Model):
    _inherit = "stock.quant"

    inventory_value = fields.Float('Inventory Value')
    category_id = fields.Many2one(
        comodel_name='product.category',
        related='product_id.categ_id',
        readonly=True,
        store=True)

    @api.onchange('inventory_quantity', 'quantity', 'inventory_value')
    def _onchange_quantity(self):
        if self.quantity >= self.inventory_quantity and self.inventory_value > 0:
            raise ValidationError(_(
                'In case quantity is greater than counted quantity, you can not set inventory value.'))

    def _apply_inventory(self):
        is_quant = self.inventory_quantity > self.quantity and True
        self = self.with_context(is_quant=is_quant, inventory_value=self.inventory_value)
        super(StockQuant, self)._apply_inventory()
        self.write({'inventory_value': 0})

    def action_print_report(self):
        records = self
        if 'active_domain' in self.env.context:
            records = self.search(self.env.context['active_domain'])
        return self.env['ir.actions.report'].search(
            [('report_name', '=', 'azi_stock.report_stock_quant')]).report_action(records, config=False)


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    lot_temp_id = fields.Many2one('stock.lot', 'Lot/Serial Number')
    lot_temp_ids = fields.Many2many('stock.lot', compute='_compute_lot_temp_ids')

    def _compute_lot_temp_ids(self):
        for record in self:
            quants = self.env['stock.quant'].search([('location_id', '=', record.location_id.id),
                                                     ('product_id', '=', record.move_id.product_id.id),
                                                     ('lot_id', '!=', False), ('quantity', '>', 0)])
            if quants:
                record.lot_temp_ids = quants.mapped('lot_id').ids
            else:
                record.lot_temp_ids = None

    @api.onchange('lot_temp_id')
    def _onchange_lot_temp(self):
        self.lot_id = self.lot_temp_id

    def _action_done(self):
        for record in self:
            if record.product_id.tracking == 'serial' and record.picking_id.picking_type_id.code == 'outgoing' and \
                    not record.lot_temp_id:
                raise ValidationError('You need to supply a Lot/Serial number '
                                      'for product %s.' % record.product_id.display_name)
            if record.picking_id.picking_type_id.code == 'internal' and record.product_id.tracking == 'serial':
                if record.lot_id:
                    location = record.lot_id.quant_ids.filtered(lambda q: q.location_id == record.location_id)
                    if not location or location.quantity < record.qty_done:
                        raise ValidationError('Serial number %s is not available in stock location %s' %
                                              (record.lot_id.name, record.location_id.display_name))
        return super(StockMoveLine, self)._action_done()


class StockMove(models.Model):
    _inherit = 'stock.move'

    def action_show_details(self):
        res = super(StockMove, self).action_show_details()
        if self.has_tracking == 'serial':
            res['context']['show_lots_m2o'] = False
        return res
