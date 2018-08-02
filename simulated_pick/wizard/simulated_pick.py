# -*- coding: utf-8 -*-
# (c) 2014 scosist
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import time
import odoo.addons.decimal_precision as dp
from odoo import models, fields, api, _
from collections import OrderedDict


class SimulatedPick(models.TransientModel):
    _name = 'simulated.pick'
    _description = 'Material Requirements Calculator'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        domain=[
            ('type', '!=', 'service'),
            ('bom_ids', '!=', False),
            ('bom_ids.type', '!=', 'phantom')
        ],
        help="Product to be produced in simulation")

    product_qty = fields.Float(
        string='Product Quantity',
        digits=dp.get_precision('Product Unit of Measure'),
        required=True,
        default=1,
        help="Quantity to be produced in simulation")

    date_planned = fields.Date(
        string='Scheduled Date',
        required=True,
        index=1,
        copy=False,
        default=time.strftime('%Y-%m-%d'),
        help="Date to simulate product completion")

    consider_plan_in = fields.Boolean(
        string='Consider Planned In',
        default=False,
        help="REMEMBER TO RUN MRP CALCULATION FIRST.\n"
             "Use MRP planned INBOUND orders as if they were actual orders.\n"
             "When simulating an entry in the Master Schedule, set the "
             "Scheduled Date 1 day earlier than the date on the master "
             "schedule entry")

    consider_plan_out = fields.Boolean(
        string='Consider Planned Out',
        default=True,
        help="REMEMBER TO RUN MRP CALCULATION FIRST.\n"
             "Use MRP planned OUTBOUND orders as if they were actual orders.\n"
             "When simulating an entry in the Master Schedule, set the "
             "Scheduled Date 1 day earlier than the date on the master "
             "schedule entry")

    def _get_plan_virt_qty(self, to_date, product):
        """Return the quantity available before consumption, and difference or change in quantity after consumption"""
        virt_qty = product.with_context(to_date=to_date).virtual_available
        plan_qty = 0
        if self.consider_plan_in or self.consider_plan_out:
            plan = product.planned_qty(to_date=self.date_planned)[product.id]
            if self.consider_plan_in:
                plan_qty += plan['qty_in']
            if self.consider_plan_out:
                plan_qty -= plan['qty_out']
        virt_qty += plan_qty
        return virt_qty

    @api.model
    def _action_compute_lines(self, product, product_qty, pick_results=None, initial_run=0, bom=None):

        pick_results = pick_results or OrderedDict()
        if initial_run:
            # TODO: call virtual_available on all products at once
            virt = self._get_plan_virt_qty(self.date_planned, product)
            on_hand_after = virt - self.product_qty
            actions = product.get_procurement_actions(orderpoint=False)
            new_pick = {
                'sim_prod_id': self.product_id.id,
                'product_id': product.id,
                'proc_action': '/'.join(actions),
                'product_qty': self.product_qty,
                'on_hand_before': virt,
                'on_hand_after': on_hand_after,
                'short': -on_hand_after if on_hand_after < 0 else 0,
            }
            pick_results[new_pick['product_id']] = new_pick

        bom = bom or self.env['mrp.bom']._bom_find(product=product)
        bom_uom_qty = product.uom_id._compute_quantity(qty=product_qty, to_unit=bom.product_uom_id)
        boms, lines = bom.explode(product, bom_uom_qty / bom.product_qty)
        for bom_line, detail in lines:
            line_prod = bom_line.product_id
            current_demand = detail['qty']
            previous_demand = pick_results.get(line_prod.id) and pick_results[line_prod.id]['product_qty'] or 0
            total_demand = current_demand + previous_demand
            if bom_line.product_id.default_code == 'X010318.-0':
                import pdb
                pdb.set_trace()
            if pick_results.get(line_prod.id):
                # product previously collected in pick_results, update qty
                on_hand_after = pick_results[line_prod.id]['on_hand_before'] - total_demand
                short = -on_hand_after if on_hand_after < 0 else 0
                pick_results[line_prod.id]['product_qty'] = total_demand
                pick_results[line_prod.id]['on_hand_after'] = on_hand_after
                pick_results[line_prod.id]['short'] = short
            else:
                # not yet collected, prep and collect in pick_results
                virt = self._get_plan_virt_qty(self.date_planned, line_prod)
                on_hand_after = virt - total_demand
                short = -on_hand_after if on_hand_after < 0 else 0
                actions = line_prod.get_procurement_actions(orderpoint=False)
                new_pick = {
                    'sim_prod_id': self.product_id.id,
                    'product_id': line_prod.id,
                    'proc_action': '/'.join(actions),
                    'product_qty': total_demand,
                    'on_hand_before': virt,
                    'on_hand_after': on_hand_after,
                    'short': short,
                }
                pick_results[line_prod.id] = new_pick

            if 'manufacture' in pick_results[line_prod.id]['proc_action']:
                line_bom = bom._bom_find(product=line_prod)
                pick_results[line_prod.id]['routing_detail'] = line_bom.routing_detail
                if line_bom and short:
                    # we only simulate demand for components when the parent comes up short
                    self._action_compute_lines(line_prod, current_demand, pick_results=pick_results, bom=line_bom)

        return pick_results

    @api.multi
    def action_compute(self):
        context = self._context

        sim_line = self.env['simulated.pick.product']
        # delete existing records in simulated.pick.product for current uid
        old_lines = sim_line.search([('create_uid', '=', self._uid), ('sim_prod_id', '=', self.product_id.id)])
        if old_lines:
            old_lines.unlink()

        # collect simulated.pick results
        new_lines = self._action_compute_lines(self.product_id, self.product_qty, initial_run=1)
        for key, line in new_lines.iteritems():
            sim_line.create(line)

        search_view_id = self.env.ref('simulated_pick.simulated_pick_product_search_form_view')
        tree_view_id = self.env.ref('simulated_pick.simulated_pick_product_tree_view')
        form_view_id = self.env.ref('simulated_pick.simulated_pick_product_form_view')
        views = [
            (tree_view_id.id, 'tree'),
            (form_view_id.id, 'form'),
        ]
        return {
            'name': _('Requirements Calculator'),
            'domain': [('create_uid', '=', self._uid), ('sim_prod_id', '=', self.product_id.id)],
            'context': context,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'simulated.pick.product',
            'type': 'ir.actions.act_window',
            'views': views,
            'view_id': False,
            'search_view_id': search_view_id.id,
        }
