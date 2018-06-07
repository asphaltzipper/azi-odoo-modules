# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round



class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def do_batch_transfer(self):
        """
        Validate a batch of internal transfers.
        Only allow Internal Transfer type.
        Only allow Available pickings.
        Only allow totally incomplete picking lines.
        Skip transfers requiring serial numbers.
        Skip transfers requiring quality checks.
        """
        for pick in self:
            if not pick.picking_type_id == self.env.ref('stock.picking_type_internal'):
                raise UserError(_('Transfers must be type "Internal Transfers". (%s)' % pick))
            if not pick.state == 'assigned':
                raise UserError(_('Transfer must be in the "Available" state. (%s)' % pick))
            if not all([x.qty_done == 0.0 for x in pick.pack_operation_ids]):
                raise UserError(_('We can only validate batches with NO completed lines. (%s)' % pick))
            if not pick.move_lines and not pick.pack_operation_ids:
                raise UserError(_('Create some Initial Demand or Mark as Todo and create some Operations. (%s)' % pick))
            picking_type = pick.picking_type_id
            serials_required = False
            if picking_type.use_create_lots or picking_type.use_existing_lots:
                for pack in pick.pack_operation_ids:
                    if pack.product_id and pack.product_id.tracking != 'none':
                        serials_required = True
                        # raise UserError(_('Lots/serials required, specify those first! (%s)' % pick))
            if pick.check_todo or serials_required:
                continue
            for pack in pick.pack_operation_ids:
                if pack.product_qty > 0:
                    this_qty = float_round(
                        pack.product_qty,
                        precision_rounding=self.product_id.uom_id.rounding)
                    pack.write({'qty_done': this_qty})
                else:
                    pack.unlink()
            pick.do_transfer()

    @api.multi
    def do_complete_qty(self):
        """
        Only allow totally incomplete picking lines.
        Skip moves requiring serial numbers.
        """
        for pick in self:
            for pack in pick.pack_operation_ids:
                if pack.qty_done == 0 and not pack.product_id.tracking != 'none':
                    this_qty = pack.product_qty
                    pack.write({'qty_done': this_qty})

    @api.multi
    def do_empty_qty(self):
        for pick in self:
            for pack in pick.pack_operation_ids:
                if pack.product_id.tracking == 'none':
                    pack.write({'qty_done': 0})


class StockPackOp(models.Model):
    _inherit = "stock.pack.operation"

    @api.multi
    def do_complete_qty_line(self):
        """
        Only allow totally incomplete picking lines.
        Skip moves requiring serial numbers.
        """
        if self.qty_done == 0 and not self.product_id.tracking != 'none':
            this_qty = self.product_qty
            self.write({'qty_done': this_qty})

    @api.multi
    def do_empty_qty_line(self):
        if self.product_id.tracking == 'none':
            self.ensure_one()
            self.write({'qty_done': 0})
