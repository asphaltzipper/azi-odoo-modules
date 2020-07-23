# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _name = "mrp.production"
    _inherit = ['mrp.production', 'barcodes.barcode_events_mixin']

    percent_available = fields.Float(
        string='Avail%',
        compute='_compute_percent_available',
        store=True)

    _barcode_scanned = fields.Char(
        string="Barcode Scanned",
        help="Value of the last barcode scanned.",
        store=False)

    @api.multi
    @api.depends('move_raw_ids.state', 'workorder_ids.move_raw_ids')
    def _compute_percent_available(self):
        for order in self:
            if order.state == 'done':
                order.percent_available = 1.0
            elif order.state == 'cancel':
                order.percent_available = 0.0
            elif not order.move_raw_ids:
                order.percent_available = 0.0
            else:
                # required_qty = sum(
                #     order.move_raw_ids.filtered(
                #         lambda r: r.state != 'cancel').mapped('product_qty'))
                # avail_qty = sum(
                #     order.move_raw_ids.filtered(
                #         lambda r: r.state != 'cancel'
                #     ).mapped('reserved_availability'))
                required_qty = len(
                    order.move_raw_ids.filtered(lambda r: r.state != 'cancel')
                )
                avail_qty = len(
                    order.move_raw_ids.filtered(lambda r: r.state == 'assigned')
                )
                order.percent_available = required_qty and \
                                          avail_qty/required_qty or 0.0

    @api.multi
    def action_production_from_barcode(self):
        self.ensure_one()
        action = self.env.ref('mrp_stock_reservation.action_production_from_barcode').read()[0]
        action['res_id'] = self.id
        return action

    def on_barcode_scanned(self, barcode):
        new_mo = self.search([('name', '=', barcode)], limit=1)
        if new_mo:
            # return an action that will load a new product in the form
            # this is done in the javascript barcode handler function
            return new_mo.action_production_from_barcode()
        prod_domain = [
            '|', ('default_code', '=', barcode),
            '|', ('mfg_code', '=', barcode),
            ('barcode', '=', barcode),
        ]
        prod_id = self.env['product.product'].search(prod_domain, limit=1)
        if not prod_id:
            raise UserError("Unknown Barcode: %s" % (barcode,))
        order_id = self.id or self._origin.id
        domain = [
            ('product_id', '=', prod_id.id),
            ('raw_material_production_id', '=', order_id)
        ]
        moves = self.env['stock.move'].search(domain)
        for move in moves:
            move._action_assign()
