# -*- coding: utf-8 -*-
# (c) 2014 scosist
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import time
import odoo.addons.decimal_precision as dp
from odoo import models, fields, api, exceptions, _
from odoo.osv import expression
from collections import OrderedDict


class SimulatedPick(models.TransientModel):
    _name = 'simulated.pick'
    _description = 'Material Requirements Calculator'

    product_id = fields.Many2one('product.product', 'Product', required=True, domain=[('type','!=','service'),('bom_ids', '!=', False),('bom_ids.type','!=','phantom')])
    product_qty = fields.Float('Product Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), required=True, default=1)
    date_planned = fields.Date('Scheduled Date', required=True, select=1, copy=False, default=time.strftime('%Y-%m-%d'))

    def _get_procurement_action(self, product):
        """
        Return true if this product should be manufactured, based on procurement rule
        We may want to add an interface to the procurement.rule model, so users can change the sequence
        """
        domain = []

        # try finding a rule on product routes
        Pull = self.env['procurement.rule']
        rule = self.env['procurement.rule']
        product_routes = product.route_ids | product.categ_id.total_route_ids
        if product_routes:
            rule = Pull.search(expression.AND([[('route_id', 'in', product_routes.ids)], domain]),
                               order='route_sequence, sequence', limit=1)

        # try finding a rule on warehouse routes
        if not rule:
            warehouse = self.env['stock.warehouse'].search([], order='id', limit=1)
            warehouse_routes = warehouse.route_ids
            if warehouse_routes:
                rule = Pull.search(expression.AND([[('route_id', 'in', warehouse_routes.ids)], domain]),
                                   order='route_sequence, sequence', limit=1)

        # try finding a rule that handles orders with no route
        if not rule:
            rule = Pull.search(expression.AND([[('route_id', '=', False)], domain]), order='sequence', limit=1)

        if not rule:
            return 'unknown'
        return rule.action

    @api.model
    def _action_compute_lines(self, product, product_qty, pick_results=None, initial_run=0, bom=None):

        pick_results = pick_results or OrderedDict()
        if initial_run:
            virt = product.with_context(to_date=self.date_planned).virtual_available
            diff = virt - self.product_qty
            new_pick = {
                'product_id': product.id,
                # TODO: handle products with multiple routes selected
                'proc_action': self._get_procurement_action(product),
                'product_qty': self.product_qty,
                'on_hand_before': virt,
                'on_hand_after': diff,
                'short': -diff if diff < 0 else 0,
            }
            pick_results[new_pick['product_id']] = new_pick

        bom = bom or self.env['mrp.bom']._bom_find(product=product)
        bom_uom_qty = product.uom_id._compute_quantity(qty=product_qty, to_unit=bom.product_uom_id)
        boms, lines = bom.explode(product, bom_uom_qty / bom.product_qty)
        for bom_line, detail in lines:
            line_prod = bom_line.product_id
            if pick_results.get(line_prod.id):
                # product previously collected in pick_results, update qty
                pick_results[line_prod.id]['product_qty'] += detail['qty']
                virt = line_prod.with_context(to_date=self.date_planned).virtual_available
                diff = virt - pick_results[line_prod.id]['product_qty']
                pick_results[line_prod.id]['on_hand_after'] = diff
                pick_results[line_prod.id]['short'] = -diff if diff < 0 else 0
            else:
                # not yet collected, prep and collect in pick_results
                virt = line_prod.with_context(to_date=self.date_planned).virtual_available
                diff = virt - detail['qty']
                new_pick = {
                    'product_id': line_prod.id,
                    'proc_action': self._get_procurement_action(line_prod),
                    'product_qty': detail['qty'],
                    'on_hand_before': virt,
                    'on_hand_after': diff,
                    'short': -diff if diff < 0 else 0,
                }
                pick_results[line_prod.id] = new_pick

            if pick_results[line_prod.id]['proc_action'] == 'manufacture':
                line_bom = bom._bom_find(product=line_prod)
                if line_bom:
                    self._action_compute_lines(line_prod, detail['qty'], pick_results=pick_results, bom=line_bom)

        return pick_results

    @api.multi
    def action_compute(self):
        context = self._context

        def ref(lookup_module, xml_id):
            proxy = self.env['ir.model.data']
            return proxy.get_object_reference(lookup_module, xml_id)

        model, search_view_id = ref('simulated_pick', 'simulated_pick_product_search_form_view')
        model, tree_view_id = ref('simulated_pick', 'simulated_pick_product_tree_view')

        pick_prod = self.env['simulated.pick.product']
        # delete existing records in simulated.pick.product for current uid
        all_pick_ids = pick_prod.search([('create_uid', '=', self._uid)])
        if all_pick_ids:
            all_pick_ids.unlink()

        # collect simulated.pick results
        all_picks = self._action_compute_lines(self.product_id, self.product_qty, initial_run=1)
        for key, pick in all_picks.iteritems():
            pick_prod.create(pick)

        views = [
            (tree_view_id, 'tree'),
        ]

        return {
            'name': _('Requirements Calculator'),
            'domain': [('create_uid', '=', self._uid)],
            'context': context,
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'simulated.pick.product',
            'type': 'ir.actions.act_window',
            'views': views,
            'view_id': False,
            'search_view_id': search_view_id,
        }
