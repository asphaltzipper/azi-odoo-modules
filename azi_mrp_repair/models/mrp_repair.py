# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare


class Repair(models.Model):
    _inherit = 'repair.order'

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
            for operation in repair.operations:
                move = Move.create(operation._prepare_stock_move(owner_id))
                moves |= move
                operation.write({'move_id': move.id, 'state': 'done'})
            move = Move.create(repair._prepare_stock_move(owner_id))
            consumed_lines = moves.mapped('move_line_ids')
            produced_lines = move.move_line_ids
            moves |= move
            moves._action_done()
            produced_lines.write({'consume_line_ids': [(6, 0, consumed_lines.ids)]})
            res[repair.id] = move.id
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
