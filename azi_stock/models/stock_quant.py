# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class StockQuant(models.Model):
    _inherit = "stock.quant"

    category_id = fields.Many2one(
        comodel_name='product.category',
        related='product_id.categ_id',
        readonly=True,
        store=True)
    value = fields.Float(compute='_compute_value',
                            groups='stock.group_stock_manager')

    # @api.constrains('location_id', 'product_id', 'lot_id')
    # def _check_internal_location_with_serial_product(self):
    #     if self.location_id.usage == 'internal'and self.product_id.tracking == 'serial':
    #         if self.lot_id:
    #             raise ValidationError('Serial number %s is not available in stock location %s' %
    #                                   (self.lot_id.name, self.location_id.display_name))
    #         else:
    #             raise ValidationError('Serial tracked item %s is not available in stock location %s' %
    #                                   (self.product_id.display_name, self.location_id.display_name))

    @api.multi
    def _compute_value(self):
        """ For FIFO valuation, compute the current accounting valuation
        using the stock moves of the product with remaining value filled,
        the accounting valuation is computed to global level, and then will
        be divided for the quantity on hand.

        Then, the value obtained from the division is an average valuation
        of the product.

        That value will be multiplied by the quantity available in the quant.

        For standard and avg method, the standard price will be multiplied
        by the quantity available in the quant.
        """

        # Just take into account the quants with usage internal and
        # that belong to the company
        for quant in self:
            if not (quant.owner_id and quant.owner_id != quant.company_id.partner_id):
                product_valuation = {quant.product_id.id: 0.0}
                product_quantity = {quant.product_id.id: 0.0}
                move_lines = self.env['stock.move.line'].search([('product_id', '=', quant.product_id.id), '|',
                                                                ('location_id', '=', quant.location_id.id),
                                                                ('location_dest_id', '=', quant.location_id.id),
                                                                ('lot_id', '=', quant.lot_id.id), '|',
                                                                ('package_id', '=', quant.package_id.id),
                                                                ('result_package_id', '=', quant.package_id.id)])
                move_ids = move_lines.mapped('move_id')
                if quant.product_id.cost_method != 'fifo':
                    product_valuation[quant.product_id.id] = quant.product_id.standard_price
                else:
                    product_valuation[quant.product_id.id] = sum(map(abs, move_ids.mapped('price_unit')))
                prod = quant.product_id
                quant.value = 0.0

                # There is no average value for the standard method. Then, the
                # standard price is multiplied directly by the quantity in the
                # quant
                if prod.cost_method != 'fifo':
                    quant.value = product_valuation[prod.id] * quant.quantity
                    continue

                # In case of FIFO, the average value of the product in the
                # moves -> sum(total_valuation) / sum(qty_on_hand), will be
                # multiplied by quantity in the quant.
                if quant.quantity > 0:
                    quant.value = (product_valuation[prod.id] * quant.quantity)

    @api.multi
    def action_print_report(self):
        records = self
        if 'active_domain' in self.env.context:
            records = self.search(self.env.context['active_domain'])
        return self.env['ir.actions.report'].search(
            [('report_name', '=', 'azi_stock.report_stock_quant')]).report_action(records, config=False)


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    lot_temp_id = fields.Many2one('stock.production.lot', 'Lot/Serial Number')
    lot_temp_ids = fields.Many2many('stock.production.lot', compute='_compute_lot_temp_ids')

    def _compute_lot_temp_ids(self):
        for record in self:
            quants = self.env['stock.quant'].search([('location_id', '=', record.location_id.id),
                                                     ('product_id', '=', record.move_id.product_id.id),
                                                     ('lot_id', '!=', False), ('quantity', '>', 0)])
            if quants:
                record.lot_temp_ids = quants.mapped('lot_id').ids

    @api.onchange('lot_temp_id')
    def _onchange_lot_temp(self):
        self.lot_id = self.lot_temp_id

    def _action_done(self):
        for record in self:
            if record.product_id.tracking == 'serial' and record.picking_id.picking_type_id.code == 'outgoing' and\
                    not record.lot_temp_id:
                raise ValidationError('You need to supply a Lot/Serial number '
                                      'for product %s.' % record.product_id.display_name)
            if record.picking_id.picking_type_id.code == 'internal' and record.product_id.tracking == 'serial':
                if record.lot_id:
                    location = record.lot_id.quant_ids.filtered(lambda q: q.location_id == record.location_id)
                    if not location or location.quantity < record.qty_done:
                        raise ValidationError('Serial number %s is not available in stock location %s' %
                                              (record.lot_id.name, record.location_id.display_name))
        return super(StockMoveLine,self)._action_done()


class StockMove(models.Model):
    _inherit = 'stock.move'

    def action_show_details(self):
        res = super(StockMove, self).action_show_details()
        if self.has_tracking == 'serial':
            res['context']['show_lots_m2o'] = False
        return res
