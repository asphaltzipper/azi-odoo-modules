# -*- coding: utf-8 -*-
# (c) 2014 scosist
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class MrpMaterialAnalysis(models.TransientModel):
    _name = 'mrp.material.analysis'
    _description = 'Material Analysis'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True)

    include_plan = fields.Boolean(
        string='Consider MRP Plan',
        default=True,
        help="REMEMBER TO RUN MRP CALCULATION FIRST.\n"
             "We will include MRP planned orders in the analysis.")

    @api.model
    def _action_compute_lines(self):
        lines = []

        # get stock moves
        move_domain = [('product_id', '=', self.product_id.id), ('state', 'not in', ['cancel', 'done'])]
        stock_moves = self.env['stock.move'].search(move_domain)
        for move in stock_moves:
            if move.location_id.usage == 'supplier':
                tx_type = 'po'
                qty_factor = 1
            elif move.location_id.usage == 'production':
                tx_type = 'mo'
                qty_factor = 1
            elif move.location_dest_id.usage == 'production':
                tx_type = 'pick'
                qty_factor = -1
            elif move.location_dest_id.usage == 'customer':
                tx_type = 'so'
                qty_factor = -1
            else:
                continue
            lines.append({
                'product_id': self.product_id.id,
                'tx_type': tx_type,
                'tx_date': move.date,
                'product_qty': qty_factor * move.product_qty,
                'available_qty': 0,
                'late': move.date < datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'status': 'actual',
                'origin': move.origin,
            })

        # get mrp planned moves
        if self.include_plan:
            plan_domain = [('product_id', '=', self.product_id.id)]
            plan_moves = self.env['mrp.material_plan'].search(plan_domain)
            for move in plan_moves:
                if move.move_type == 'supply' and move.make:
                    tx_type = 'pmo'
                    qty_factor = 1
                elif move.move_type == 'supply' and not move.make:
                    tx_type = 'ppo'
                    qty_factor = 1
                elif move.move_type == 'demand':
                    tx_type = 'ppick'
                    qty_factor = -1
                else:
                    continue
                lines.append({
                    'product_id': self.product_id.id,
                    'tx_type': tx_type,
                    'tx_date': move.date_finish,
                    'product_qty': qty_factor * move.product_qty,
                    'available_qty': 0,
                    'late': move.date_finish < datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'status': 'planned',
                    'origin': move.origin,
                })

        return lines

    @api.multi
    def action_compute(self):

        # clear old analysis lines
        analysis_line = self.env['mrp.material.analysis.line']
        # delete existing records in mrp.material.analysis for current uid
        old_lines = analysis_line.search([('create_uid', '=', self._uid), ('product_id', '=', self.product_id.id)])
        if old_lines:
            old_lines.unlink()

        # create new analysis lines
        all_lines = self._action_compute_lines()
        for line in all_lines:
            analysis_line.create(line)

        # sort and compute running inventory level (qty available)
        virt_qty = self.product_id.qty_available
        new_lines = analysis_line.search([('create_uid', '=', self._uid), ('product_id', '=', self.product_id.id)])
        for line in new_lines.sorted():
            virt_qty += line.product_qty
            line.write({'available_qty': virt_qty})

        search_view_id = self.env.ref('mrp_material_analysis.mrp_material_analysis_line_view_search')
        tree_view_id = self.env.ref('mrp_material_analysis.mrp_material_analysis_line_view_tree')
        form_view_id = self.env.ref('mrp_material_analysis.mrp_material_analysis_line_view_form')
        graph_view_id = self.env.ref('mrp_material_analysis.mrp_material_analysis_line_view_graph')
        pivot_view_id = self.env.ref('mrp_material_analysis.mrp_material_analysis_line_view_pivot')
        views = [
            (tree_view_id.id, 'tree'),
            (form_view_id.id, 'form'),
            (graph_view_id.id, 'graph'),
            (pivot_view_id.id, 'pivot'),
        ]
        return {
            'name': _('Material Analysis'),
            'domain': [('create_uid', '=', self._uid), ('product_id', '=', self.product_id.id)],
            'context': self._context,
            'view_type': 'form',
            'view_mode': 'tree,form,graph,pivot',
            'res_model': 'mrp.material.analysis.line',
            'type': 'ir.actions.act_window',
            'views': views,
            'view_id': False,
            'search_view_id': search_view_id.id,
        }
