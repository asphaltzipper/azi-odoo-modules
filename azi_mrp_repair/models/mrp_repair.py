# -*- coding: utf-8 -*-
import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare


class Repair(models.Model):
    _inherit = 'repair.order'

    inventory_revaluation_id = fields.Many2one('stock.inventory.revaluation', 'Inventory Revaluation')

    def _prepare_stock_move(self, owner_id=None):
        self.ensure_one()
        res = {
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id or self.product_id.uom_id.id,
            'product_uom_qty': self.product_qty,
            'partner_id': self.address_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_id.id,
            'move_line_ids': [(0, 0, {'product_id': self.product_id.id,
                                      'lot_id': self.lot_id.id,
                                      'product_uom_qty': 0,  # bypass reservation here
                                      'product_uom_id': self.product_uom.id or self.product_id.uom_id.id,
                                      'qty_done': self.product_qty,
                                      'package_id': False,
                                      'result_package_id': False,
                                      'owner_id': owner_id,
                                      'location_id': self.location_id.id,  # TODO: owner stuff
                                      'location_dest_id': self.location_id.id, })],
            'repair_id': self.id,
            'origin': self.name,
        }
        return res

    @api.multi
    def action_repair_done(self):
        """ Overridden for the purpose of creating a mechanism to modify the values set on the stock move
        Creates stock move for operation and stock move for final product of repair order.
        @return: Move ids of final products

        """
        if self.filtered(lambda repair: not repair.repaired):
            raise UserError(_("Repair must be repaired in order to make the product moves."))
        res = {}
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        Move = self.env['stock.move']
        for repair in self:
            owner_id = False
            available_qty_owner = self.env['stock.quant']._get_available_quantity(repair.product_id, repair.location_id,
                                                                                  repair.lot_id,
                                                                                  owner_id=repair.partner_id,
                                                                                  strict=True)
            if float_compare(available_qty_owner, repair.product_qty, precision_digits=precision) >= 0:
                owner_id = repair.partner_id.id
            moves = self.env['stock.move']
            produced_lines = self.env['stock.move.line']
            for operation in repair.operations:
                move = Move.create(operation._prepare_stock_move(owner_id))
                moves |= move
                operation.write({'move_id': move.id, 'state': 'done'})
            move = Move.create(repair._prepare_stock_move(owner_id))
            consumed_lines = moves.mapped('move_line_ids')
            produced_lines |= move.move_line_ids
            moves |= move
            moves._action_done()
            produced_lines.write({'consume_line_ids': [(6, 0, consumed_lines.ids)]})
            res[repair.id] = move.id
            if not repair.partner_id and repair.location_id.usage == 'internal':
                product_values = sum(repair.operations.filtered(lambda o: o.move_id.account_move_ids).mapped('move_id.value'))
                if product_values:
                    new_value = repair.product_id.stock_value + product_values
                    valuation_account_id = repair.product_id.categ_id.property_stock_valuation_account_id.id
                    revaluation_vals = {
                        'revaluation_type': 'inventory_value',
                        'product_id': repair.product_id.id,
                        'new_value': new_value,
                        'journal_id': self.env['account.journal'].search([('type', '=', 'general')], limit=1).id,
                        'increase_account_id': valuation_account_id,
                        'decrease_account_id': valuation_account_id,
                    }
                    revaluation = self.env['stock.inventory.revaluation'].create(revaluation_vals)
                    repair.inventory_revaluation_id = revaluation
                    if repair.product_id.categ_id.property_cost_method == 'fifo':
                        product_move = moves.filtered(lambda m: m.product_id == repair.product_id)
                        if product_move:
                            revaluation.reval_move_ids = [(0, _, {'move_id': product_move[0].id,
                                                                  'new_value': new_value})]
                    revaluation.button_post()
        return res


class RepairLine(models.Model):
    _inherit = 'repair.line'

    def _prepare_stock_move(self, owner_id=None):
        """ We change the name of the stock move to be the name of the repair
        order, instead of the product display name """
        self.ensure_one()
        res = {
            'name': self.repair_id.name,
            'product_id': self.product_id.id,
            'product_uom_qty': self.product_uom_qty,
            'product_uom': self.product_uom.id,
            'partner_id': self.repair_id.address_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'move_line_ids': [(0, 0, {'product_id': self.product_id.id,
                                      'lot_id': self.lot_id.id,
                                      'product_uom_qty': 0,  # bypass reservation here
                                      'product_uom_id': self.product_uom.id,
                                      'qty_done': self.product_uom_qty,
                                      'package_id': False,
                                      'result_package_id': False,
                                      'owner_id': owner_id,
                                      'location_id': self.location_id.id,  # TODO: owner stuff
                                      'location_dest_id': self.location_dest_id.id, })],
            'repair_id': self.repair_id.id,
            'origin': self.repair_id.name,
        }
        return res

    @api.onchange('type', 'repair_id')
    def onchange_operation_type_azi(self):
        if self.type == 'remove':
            self.price_unit = 0.0
            self.tax_id = False
            args = self.repair_id.company_id and [('company_id', '=', self.repair_id.company_id.id)] or []
            warehouse = self.env['stock.warehouse'].search(args, limit=1)
            self.location_dest_id = warehouse.lot_stock_id
            self.location_id = self.env['stock.location'].search([('usage', '=', 'production')], limit=1).id
