# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round


class StockPicking(models.Model):
    _inherit = "stock.picking"

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
            if not all([x.qty_done == 0.0 for x in pick.move_line_ids_without_package]):
                raise UserError(_('We can only validate batches with NO completed lines. (%s)' % pick))
            if not pick.move_ids_without_package and not pick.move_line_ids_without_package:
                raise UserError(_('Create some Initial Demand or Mark as Todo and create some Operations. (%s)' % pick))
            picking_type = pick.picking_type_id
            serials_required = False
            if picking_type.use_create_lots or picking_type.use_existing_lots:
                for pack in pick.move_line_ids_without_package:
                    if pack.product_id and pack.product_id.tracking != 'none':
                        serials_required = True
                        # raise UserError(_('Lots/serials required, specify those first! (%s)' % pick))
            if pick.quality_check_todo or serials_required:
                continue
            for pack in pick.move_line_ids_without_package:
                if pack.reserved_uom_qty > 0:
                    this_qty = float_round(
                        pack.reserved_uom_qty,
                        precision_rounding=self.product_id.uom_id.rounding)
                    pack.write({'qty_done': this_qty})
                else:
                    pack.unlink()
            pick._action_done()

    def do_complete_qty(self):
        """
        Only allow totally incomplete picking lines.
        Skip moves requiring serial numbers.
        """
        for pick in self:
            for pack in pick.move_line_ids_without_package:
                if pack.qty_done == 0 and not pack.product_id.tracking != 'none':
                    this_qty = pack.reserved_uom_qty
                    pack.write({'qty_done': this_qty})

    def do_empty_qty(self):
        for pick in self:
            for pack in pick.move_line_ids_without_package:
                if pack.product_id.tracking == 'none':
                    pack.write({'qty_done': 0})


class StockPackOp(models.Model):
    _inherit = "stock.move.line"

    def do_complete_qty_line(self):
        """
        Only allow totally incomplete picking lines.
        Skip moves requiring serial numbers.
        """
        if self.qty_done == 0 and not self.product_id.tracking != 'none':
            this_qty = self.reserved_uom_qty
            self.write({'qty_done': this_qty})

    def do_empty_qty_line(self):
        if self.product_id.tracking == 'none':
            self.ensure_one()
            self.write({'qty_done': 0})
