# -*- coding: utf-8 -*-
# See __openerp__.py file for full copyright and licensing details.

from datetime import datetime
from openerp import models, fields, SUPERUSER_ID
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import openerp
import logging
_logger = logging.getLogger(__name__)


class procurement_order(models.Model):
    _inherit = 'procurement.order'
    _order = 'priority desc, date_start, date_planned, id asc'

    date_start = fields.Datetime('Start Date', required=False, select=True)

    # stock/procurement,procurement/procurement
    def run_scheduler(self, cr, uid, use_new_cursor=False, company_id=False, context=None):
        '''
        Call the scheduler in order to check the running procurements (this REPLACES run_scheduler to eliminate
        automatic execution of run for confirmed procurements), to check the minimum stock rules and the availability
        of moves. This function is intended to be run for all the companies at the same time, so we run functions as
        SUPERUSER to avoid intercompanies and access rights issues.
        @param self: The object pointer
        @param cr: The current row, from the database cursor,
        @param uid: The current user ID for security checks
        @param ids: List of selected IDs
        @param use_new_cursor: if set, use a dedicated cursor and auto-commit after processing each procurement.
            This is appropriate for batch jobs only.
        @param context: A standard dictionary for contextual values
        @return:  Dictionary of values
        '''
        if context is None:
            context = {}
        try:
            if use_new_cursor:
                cr = openerp.registry(cr.dbname).cursor()

            # Check if running procurements are done
            offset = 0
            dom = [('state', '=', 'running')]
            if company_id:
                dom += [('company_id', '=', company_id)]
            prev_ids = []
            while True:
                ids = self.search(cr, SUPERUSER_ID, dom, offset=offset, context=context)
                if not ids or prev_ids == ids:
                    break
                else:
                    prev_ids = ids
                self.check(cr, SUPERUSER_ID, ids, autocommit=use_new_cursor, context=context)
                if use_new_cursor:
                    cr.commit()

            move_obj = self.pool.get('stock.move')

            #Minimum stock rules
            self._procure_orderpoint_confirm(cr, SUPERUSER_ID, use_new_cursor=use_new_cursor, company_id=company_id, context=context)

            #Search all confirmed stock_moves and try to assign them
            confirmed_ids = move_obj.search(cr, uid, [('state', '=', 'confirmed')], limit=None, order='priority desc, date_expected asc', context=context)
            for x in xrange(0, len(confirmed_ids), 100):
                move_obj.action_assign(cr, uid, confirmed_ids[x:x + 100], context=context)
                if use_new_cursor:
                    cr.commit()

            if use_new_cursor:
                cr.commit()
        finally:
            if use_new_cursor:
                try:
                    cr.close()
                except Exception:
                    pass
        return {}

    def run(self, cr, uid, ids, autocommit=False, context=None):
        super(procurement_order, self).run(cr, uid, ids, autocommit, context=context)

    # procurement/procurement:run_scheduler
    def run_procurement(self, cr, uid, ids, use_new_cursor=False, context=None):
        context = context or {}
        try:
            if use_new_cursor:
                cr = openerp.registry(cr.dbname).cursor()

            # Run selected procurements
            dom = [('id', 'in', ids), ('state', '=', 'confirmed')]
            prev_ids = []
            while True:
                ids = self.search(cr, SUPERUSER_ID, dom, context=context)
                if not ids or prev_ids == ids:
                    break
                else:
                    prev_ids = ids
                self.run(cr, SUPERUSER_ID, ids, autocommit=use_new_cursor, context=context)
                if use_new_cursor:
                    cr.commit()

            # Check if selected running procurements are done
            offset = 0
            dom = [('id', 'in', ids), ('state', '=', 'running')]
            prev_ids = []
            while True:
                ids = self.search(cr, SUPERUSER_ID, dom, offset=offset, context=context)
                if not ids or prev_ids == ids:
                    break
                else:
                    prev_ids = ids
                self.check(cr, SUPERUSER_ID, ids, autocommit=use_new_cursor, context=context)
                if use_new_cursor:
                    cr.commit()
        finally:
            if use_new_cursor:
                try:
                    cr.close()
                except Exception:
                    pass
        return {}

    # stock/procurement,mrp_time_bucket/mrp_time_bucket
    def _prepare_orderpoint_procurement(self, cr, uid, orderpoint, product_qty, context=None):
        res = super(procurement_order, self)._prepare_orderpoint_procurement(cr, uid, orderpoint, product_qty, context=context)
        res['date_start'] = self._get_procurement_date_start(cr, uid, orderpoint, context['bucket_date'], context=context)
        _logger.info(" IN res: %s", res)
        return res

    def _prepare_outbound_procurement(self, cr, uid, orderpoint, product, product_qty, product_uom, context=None):
        all_parent_location_ids = self._find_parent_locations(cr, uid, orderpoint, context=context)
        location_domain = [('location_id', 'in', all_parent_location_ids)]
        child_orderpoint_id = self.pool.get('stock.warehouse.orderpoint').search(cr, uid, [
            ('product_id', '=', product.id),
            ('warehouse_id', '=', orderpoint.warehouse_id.id),
            ] + location_domain, limit=1)
        # dirty hack to pretend orderpoint is procurement in order to use _search_suitable_rule
        orderpoint.route_ids = []
        parent_rule_id = self._search_suitable_rule(cr, uid, orderpoint, location_domain, context=context)
        del orderpoint.route_ids
        parent_location_id = parent_rule_id and self.pool.get('procurement.rule').browse(cr, uid, parent_rule_id)[0].location_src_id or False
        res = {
            'name': product.product_tmpl_id.name,
            'date_planned': context['bom_effectivity_date'],
            'product_id': product.id,
            'product_qty': product_qty,
            'company_id': product.product_tmpl_id.company_id.id,
            'product_uom': product_uom,
            'location_id': parent_location_id and parent_location_id.id or product.property_stock_production.id,
            'origin': 'OUT/PROC/' + '%%0%sd' % 5 % context['parent_proc_id'],
            'warehouse_id': orderpoint.warehouse_id.id,
            'date_start': context['bom_effectivity_date'],
            'orderpoint_id': child_orderpoint_id and child_orderpoint_id[0] or False,
        }
        _logger.info("OUT res: %s", res)
        return res

    # override mrp_time_bucket/mrp_time_bucket
    def _process_procurement(self, cr, uid, ids, context=None):
        # REPLACE _process_procurement to eliminate automatic execution of run for confirmed procurements
        pass

    # mrp_time_bucket/mrp_time_bucket
    def _plan_orderpoint_procurement(self, cr, uid, op, qty_rounded, context=None):
        context = context or {}
        proc_id = super(procurement_order, self)._plan_orderpoint_procurement(cr, uid, op, qty_rounded, context=context)
        proc_ids = []
        proc_ids.append(proc_id)
        if proc_id:
            bom_obj = self.pool.get('mrp.bom')
            bom_id = bom_obj._bom_find(cr, uid, product_id=op.product_id.id, context=context)
            if bom_id:
                uom_obj = self.pool.get('product.uom')
                procurement_obj = self.pool.get('procurement.order')
                proc_point = procurement_obj.browse(cr, uid, proc_id)
                bom_point = bom_obj.browse(cr, uid, bom_id)
                # get components and workcenter_lines from BoM structure
                factor = uom_obj._compute_qty(cr, uid, proc_point.product_uom.id, proc_point.product_qty, bom_point.product_uom.id)
                # product_lines, workcenter_lines (False)
                #context['bom_effectivity_date'] = proc_point.date_start
                res = bom_obj._bom_explode(cr, uid, bom_point, proc_point.product_id, factor / bom_point.product_qty, context=context)
                # product_lines
                results = res[0]
                context['parent_proc_id'] = proc_id
                # process procurements for results
                for product in results:
                    product_obj = self.pool.get('product.product')
                    product_point = product_obj.browse(cr, uid, product['product_id'])
                    proc_id += procurement_obj.create(cr, uid,
                                                    self._prepare_outbound_procurement(cr, uid, op, product_point, product['product_qty'], product['product_uom'], context=context),
                                                    context=context)
                    proc_id and proc_ids.append(proc_id) or False
                #context.pop('bom_effectivity_date')
                context.pop('parent_proc_id')
        return proc_ids

    # stock/procurement,mrp_time_bucket/mrp_time_bucket
    def _procure_orderpoint_confirm(self, cr, uid, use_new_cursor=False, company_id = False, context=None):
        # delete all procurements matching
        #   created by engine
        #   in confirmed state
        #   not linked to any RFQ or MO
        procurement_obj = self.pool.get('procurement.order')
        dom = [('state', '=', 'confirmed'),
               ('purchase_line_id', '=', False),
               ('production_id', '=', False),
               '|', ('origin', 'like', 'OP/'), ('origin', 'like', 'OUT/')]
        proc_ids = procurement_obj.search(cr, uid, dom) or []
        if proc_ids:
            procurement_obj.cancel(cr, SUPERUSER_ID, proc_ids, context=context)
            procurement_obj.unlink(cr, SUPERUSER_ID, proc_ids, context=context)
            if use_new_cursor:
                cr.commit()

        super(procurement_order, self)._procure_orderpoint_confirm(cr, uid, use_new_cursor, company_id, context=context)
