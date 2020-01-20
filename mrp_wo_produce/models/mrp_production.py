# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.multi
    def open_wo_produce(self):
        self.ensure_one()
        action = self.env.ref('mrp_wo_produce.act_mrp_wo_produce_wizard').read()[0]
        return action

    @api.multi
    def post_inventory(self):
        for order in self:
            # The default behavior is to cancel stock moves when the serial number is not specified
            # We don't want to allow the user to post inventory without specifying a serial number for all tracked
            # components.  If we are going to build without the tracked component, then cancel the stock move.  If we
            # actually have the component, then do an inventory adjustment or something.
            serial_moves = order.move_raw_ids\
                .filtered(lambda x: x.state not in ('done', 'cancel') and x.product_id.tracking == 'serial')
            for move_lot in serial_moves.mapped('active_move_line_ids'):
                if not move_lot.lot_id or not move_lot.qty_done:
                    raise UserError(_('You should provide a lot for a component'))
        return super(MrpProduction, self).post_inventory()
