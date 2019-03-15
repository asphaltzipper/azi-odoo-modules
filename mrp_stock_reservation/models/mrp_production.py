# -*- coding: utf-8 -*-

from odoo import fields, models, api


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    kit_done = fields.Boolean(
        string='Kit Done',
        required=True,
        default=False,
        help="Parts kit is complete, and has been moved to starting workcenter")

    percent_available = fields.Float(
        string='Avail%',
        compute='_compute_percent_available',
        store=True)

    @api.multi
    @api.depends('move_raw_ids.state', 'move_raw_ids.partially_available', 'workorder_ids.move_raw_ids')
    def _compute_percent_available(self):
        for order in self:
            if order.state == 'done':
                order.percent_available = 1.0
            elif order.state == 'cancel':
                order.percent_available = 0.0
            elif not order.move_raw_ids:
                order.percent_available = 0.0
            else:
                required_qty = sum(order.move_raw_ids.filtered(lambda r: r.state != 'cancel').mapped('product_qty'))
                avail_qty = sum([sum(move.reserved_quant_ids.mapped('qty')) for move in order.move_raw_ids])
                avail_qty += sum(order.move_raw_ids.filtered(lambda r: r.state != 'cancel' and r.product_id.type == 'consu').mapped('product_qty'))
                order.percent_available = avail_qty/required_qty
