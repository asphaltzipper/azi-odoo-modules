from odoo import models, fields, api, _
from odoo.tools import float_compare
from odoo.exceptions import ValidationError, UserError


class MRPComponentSerial(models.TransientModel):
    _name = 'mrp.component.serial'
    _description = 'Lot/Serial Tracking'

    production_id = fields.Many2one('mrp.production', 'Manufacturing Order')
    component_serial_line_ids = fields.One2many('mrp.component.serial.line', 'component_serial_id',
                                                'Component Tracked Lines')

    @api.model
    def default_get(self, fields):
        res = super(MRPComponentSerial, self).default_get(fields)
        if self._context and self._context.get('active_model', '') == 'mrp.production' and self._context.get(
                'active_id'):
            production = self.env['mrp.production'].browse(self._context['active_id'])
        res.update({
            'production_id': production.id,
        })
        return res

    @api.onchange('production_id')
    def onchange_production(self):
        self.load_lines()

    def load_lines(self):
        component_lines = []
        for move in self.production_id.move_raw_ids.filtered(lambda m: m.state not in ('done', 'cancel') and
                                                       m.product_id.tracking != 'none'):
            qty = move.product_uom_qty - move.quantity_done
            res_qty = move.reserved_availability - move.quantity_done
            res_lots = move.move_line_ids.filtered(lambda x: x.state not in ['done', 'cancel']).mapped('lot_id').ids
            if move.product_id.tracking == 'serial':
                while float_compare(qty, 0.0, precision_rounding=move.product_uom.rounding) > 0:
                    component_lines.append({
                        'move_id': move.id,
                        'qty_to_consume': 1.0,
                        'qty_done': res_lots and 1 or 0,
                        'lot_id': res_lots and res_lots.pop() or False,
                        'product_id': move.product_id.id,
                        'qty_reserved': 1.0,
                    })
                    qty -= 1
            else:
                component_lines.append({
                    'move_id': move.id,
                    'qty_to_consume': qty,
                    'qty_done': res_lots and qty or 0,
                    'lot_id': res_lots and res_lots.pop() or False,
                    'product_id': move.product_id.id,
                    'qty_reserved': res_qty,
                })
        self.component_serial_line_ids = [(5,)] + [(0, 0, x) for x in component_lines]
        return True

    def assign_serial(self):
        last_workorder = self.production_id.workorder_ids and self.production_id.workorder_ids[-1]
        move_line_ids = self.component_serial_line_ids.mapped('move_id.move_line_ids')
        move_line_ids.unlink()
        for line in self.component_serial_line_ids:
            if not line.lot_id:
                raise UserError(_('Please enter a lot or serial number for component %s !' % line.product_id.display_name))
            if float_compare(line.qty_to_consume, line.qty_done, precision_rounding=line.product_id.uom_id.rounding) != 0:
                raise UserError(_('Please correct Consumed quantity for lot %s !' % line.lot_id.display_name))
            line.move_id.move_line_ids.create({
                'move_id': line.move_id.id,
                'lot_id': line.lot_id.id,
                'reserved_uom_qty': 0,
                'product_uom_id': line.move_id.product_uom.id,
                'qty_done': line.qty_done,
                'production_id': self.production_id.id,
                'workorder_id': line.move_id.workorder_id.id or last_workorder.id,
                'product_id': line.product_id.id,
                'location_id': line.move_id.location_id.id,
                'location_dest_id': line.move_id.location_dest_id.id,
            })


class MRPComponentSerialLine(models.TransientModel):
    _name = 'mrp.component.serial.line'
    _description = 'Lot/Serial Tracking Lines'

    component_serial_id = fields.Many2one('mrp.component.serial', 'Components')
    move_id = fields.Many2one('stock.move', 'Move')
    move_line_id = fields.Many2one('stock.move.line', 'Move Line')
    product_id = fields.Many2one('product.product', 'Product', related='move_id.product_id')
    tracking = fields.Selection(related='product_id.tracking', string='Tracking')
    product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure', related='move_id.product_id.uom_id')
    qty_to_consume = fields.Float('To Consume', digits='Product Unit of Measure')
    qty_done = fields.Float('Produced')
    qty_reserved = fields.Float('Reserved')
    lot_id = fields.Many2one('stock.lot', 'Lot/Serial Number')

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        res = {}
        if self.product_id.tracking == 'serial':
            if self.lot_id:
                self.qty_done = 1
            else:
                self.qty_done = 0
        return res

    @api.constrains('component_serial_id', 'lot_id', 'tracking')
    def check_unique_serial(self):
        for record in self:
            if record.component_serial_id and record.lot_id:
                serial_lines = self.search([
                    ('component_serial_id', '=', record.component_serial_id.id),
                    ('lot_id', '=', record.lot_id.id),
                    ('id', '!=', record.id)
                ])
                if serial_lines:
                    raise ValidationError(
                        f"The serial number {record.lot_id.name} used for component {record.product_id.display_name} "
                        f"has already been consumed")
