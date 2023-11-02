# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
import math


class AddRawMove(models.TransientModel):
    _name = 'add.raw.move'
    _description = 'Add Raw Material'

    production_id = fields.Many2one(
        comodel_name='mrp.production',
        string='Manufacturing Order',
        required=True)
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='RM Product',
        required=True,
        domain=[('type', 'in', ['product', 'consu'])])
    product_qty = fields.Float(
        string='Quantity To Consume',
        digits=dp.get_precision('Product Unit of Measure'),
        required=True)

    @api.model
    def default_get(self, fields):
        res = super(AddRawMove, self).default_get(fields)
        if 'production_id' in fields\
                and not res.get('production_id')\
                and self._context.get('active_model') == 'mrp.production'\
                and self._context.get('active_id'):
            res['production_id'] = self._context['active_id']
        if 'product_qty' in fields\
                and not res.get('product_qty')\
                and res.get('production_id'):
            res['product_qty'] = self.env['mrp.production'].browse(res['production_id']).product_qty
        return res

    def _generate_component_moves(self, exploded_lines):
        moves = self.env['stock.move']
        for bom_line, line_data in exploded_lines:
            moves += self._generate_component_move(bom_line, line_data)
        return moves

    def _generate_component_move(self, bom_line, line_data):
        quantity = line_data['qty']
        # alt_op needed for the case when you explode phantom bom and all the
        # lines will be consumed in the operation given by the parent bom line
        alt_op = line_data['parent_line'] and line_data['parent_line'].operation_id.id or False
        if bom_line.child_bom_id and bom_line.child_bom_id.type == 'phantom':
            return self.env['stock.move']
        if bom_line.product_id.type not in ['product', 'consu']:
            return self.env['stock.move']
        source_location = self.production_id.location_src_id
        original_quantity = self.production_id.product_qty - self.production_id.qty_produced
        data = {
            'added_rm': True,
            'name': self.production_id.name,
            'date': self.production_id.date_planned_start,
            'date_deadline': self.production_id.date_planned_start,
            'bom_line_id': bom_line.id,
            'product_id': bom_line.product_id.id,
            'product_uom_qty': quantity,
            'product_uom': bom_line.product_uom_id.id,
            'location_id': source_location.id,
            'location_dest_id': self.product_id.property_stock_production.id,
            'raw_material_production_id': self.production_id.id,
            'company_id': self.production_id.company_id.id,
            'operation_id': bom_line.operation_id.id or alt_op,
            'price_unit': bom_line.product_id.standard_price,
            'procure_method': 'make_to_stock',
            'origin': self.production_id.name,
            'warehouse_id': source_location.warehouse_id.id,
            'group_id': self.production_id.procurement_group_id.id,
            'propagate_cancel': self.production_id.propagate_cancel,
            'unit_factor': quantity / original_quantity,
        }
        return self.env['stock.move'].create(data)

    def _generate_raw_move(self):
        source_location = self.production_id.location_src_id
        data = {
            'added_rm': True,
            'name': self.production_id.name,
            'date': self.production_id.date_planned_start,
            'date_deadline': self.production_id.date_planned_start,
            'product_id': self.product_id.id,
            'product_uom_qty': self.product_qty,
            'product_uom': self.product_id.uom_id.id,
            'location_id': source_location.id,
            'location_dest_id': self.production_id.product_id.with_company(self.production_id.company_id).property_stock_production.id,
            'raw_material_production_id': self.production_id.id,
            'company_id': self.production_id.company_id.id,
            'price_unit': self.product_id.standard_price,
            'procure_method': 'make_to_stock',
            'origin': self.production_id.name,
            'warehouse_id': source_location.warehouse_id.id,
            'group_id': self.production_id.procurement_group_id.id,
            'propagate_cancel': self.production_id.propagate_cancel,
            'unit_factor': self.product_qty / self.production_id.product_qty,
        }
        return self.env['stock.move'].create(data)

    def button_add_raw_move(self):
        self.ensure_one()
        if self.production_id.state in ['done', 'cancel']:
            raise UserError(_("Production is complete for %s") % self.production_id.name)

        bom = self.env['mrp.bom']._bom_find(
            products=self.product_id,
            picking_type=self.production_id.picking_type_id,
            company_id=self.production_id.company_id.id)
        bom = bom.get(self.product_id, False)

        if bom and bom.type == 'phantom':
            boms, lines = bom.explode(
                self.product_id,
                self.product_qty,
                picking_type=bom.picking_type_id)
            moves = self._generate_component_moves(lines)
        else:
            moves = self._generate_raw_move()

        # Check for all draft moves whether they are mto or not
        moves._adjust_procure_method()
        moves._action_confirm()
        moves._action_assign()
        return {}
