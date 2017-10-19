# -*- coding: utf-8 -*-

from odoo import api, models


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.multi
    def action_done(self):
        # transition the serial number state based on move destination location
        serial_transitions = ['internal', 'inventory', 'production', 'customer']
        for move in self:
            for sn in move.lot_ids.filtered(lambda x: x.product_id.tracking == 'serial'):
                if move.move_dest_id.usage in serial_transitions:
                    sn.state = move.move_dest_id.usage
        return super(StockMove, self).action_done()
