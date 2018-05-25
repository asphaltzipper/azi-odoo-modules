# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Repair(models.Model):
    _inherit = 'mrp.repair'

    def _prepare_stock_move(self):
        self.ensure_one()
        res = {
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id or self.product_id.uom_id.id,
            'product_uom_qty': self.product_qty,
            'partner_id': self.address_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'restrict_lot_id': self.lot_id.id,
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
        Move = self.env['stock.move']
        for repair in self:
            moves = self.env['stock.move']
            for operation in repair.operations:
                move = Move.create(operation._prepare_stock_move())
                moves |= move
                operation.write({'move_id': move.id, 'state': 'done'})
            move = Move.create(repair._prepare_stock_move())
            moves |= move
            moves.action_done()
            res[repair.id] = move.id
        return res


class RepairLine(models.Model):
    _inherit = 'mrp.repair.line'

    def _prepare_stock_move(self):
        """ We change the name of the stock move to be the name of the repair
        order, instead of the product display name """
        self.ensure_one()
        res = {
            'name': self.repair_id.name,
            'product_id': self.product_id.id,
            'restrict_lot_id': self.lot_id.id,
            'product_uom_qty': self.product_uom_qty,
            'product_uom': self.product_uom.id,
            'partner_id': self.address_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
        }
        return res
