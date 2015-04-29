# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP Module
#    
#    Copyright (C) 2014 Asphalt Zipper, Inc.
#    Author scosist
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from datetime import datetime
from openerp import models, fields, api, SUPERUSER_ID
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, \
    DEFAULT_SERVER_DATE_FORMAT
import openerp


class stock_warehouse_orderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    def subtract_procurements(self, cr, uid, orderpoint, context=None):
        qty = super(stock_warehouse_orderpoint, self).subtract_procurements(cr, uid, orderpoint, context=context)
        uom_obj = self.pool.get('product.uom')
        dom = [('product_id','=',orderpoint.product_id.id),('origin','like','OUT/')]
        procurement_obj = self.pool.get('procurement.order')
        proc_ids = procurement_obj.search(cr, uid, dom)
        for procurement in procurement_obj.browse(cr, uid, proc_ids, context=context):
            if procurement.state in ('cancel', 'done'):
                continue
            procurement_qty = uom_obj._compute_qty_obj(cr, uid, procurement.product_uom, procurement.product_qty, procurement.product_id.uom_id, context=context)
            qty -= procurement_qty
        return qty


class procurement_order(models.Model):
    _inherit = 'procurement.order'
    _order = 'priority desc, date_start, date_planned, id asc'

    date_start = fields.Datetime('Start Date', required=False, select=True)

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

    def run_procurement(self, cr, uid, ids, use_new_cursor=False, context=None):
        context = context or {}
        import pdb
        pdb.set_trace()
        try:
            if use_new_cursor:
                cr = openerp.registry(cr.dbname).cursor()

            # Run selected procurements
            dom = [('id', 'in', ids), ('state', '=', 'confirmed')]
            prev_ids = []
            while True:
                ids = self.search(cr, SUPERUSER_ID, dom, context=context)
                if not ids or prev_ids ==ids:
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

    def run(self, cr, uid, ids, autocommit=False, context=None):
        super(procurement_order, self).run(cr, uid, ids, autocommit, context=context)

    def _get_procurement_date_start(self, cr, uid, modelpoint, to_date, context=None):
        if 'child_to_date' in context:
            bucket_delay = 0
        else:
            bucket_delay = self._get_bucket_delay(cr, uid, context=context)
        seller_delay = 0.0
        produce_delay = 0.0
        if modelpoint._name == 'stock.warehouse.orderpoint':
            seller_delay = modelpoint.product_id.seller_delay
            produce_delay = modelpoint.product_id.produce_delay
        if modelpoint._name == 'product.product':
            seller_delay = modelpoint.seller_delay
            produce_delay = modelpoint.produce_delay
        date_start = datetime.combine(datetime.strptime(to_date,DEFAULT_SERVER_DATE_FORMAT) - relativedelta(days=bucket_delay + seller_delay + produce_delay),datetime.min.time())
        return date_start.strftime(DEFAULT_SERVER_DATE_FORMAT)

    def _prepare_orderpoint_procurement(self, cr, uid, orderpoint, product_qty, context=None):
        res = super(procurement_order, self)._prepare_orderpoint_procurement(cr, uid, orderpoint, product_qty, context=context)
        res['date_start'] = self._get_procurement_date_start(cr, uid, orderpoint, context['to_date'], context=context)
        return res

    def _prepare_outbound_procurement(self, cr, uid, product, product_qty, product_uom, context=None):
        return {
            'name': product.product_tmpl_id.name,
            'date_planned': self._get_procurement_date_planned(cr, uid, context['child_to_date'], context=context),
            'product_id': product.id,
            'product_qty': product_qty,
            'company_id': product.product_tmpl_id.company_id.id,
            'product_uom': product_uom,
            'location_id': self.pool.get('ir.model.data').xmlid_to_res_id(cr, uid, 'stock.location_production'),
            'origin': 'OUT/BOM/' + '%%0%sd' % 5 % context['parent_bom_id'],
            #'warehouse_id': ,
            'date_start': self._get_procurement_date_start(cr, uid, product, context['child_to_date'], context=context),
        }

    def _process_procurement(self, cr, uid, proc_id, context=None):
        # REPLACE _process_procurement to eliminate automatic execution of run for confirmed procurements
        self.check(cr, uid, [proc_id])

    def _create_orderpoint_procurement(self, cr, uid, order_point, qty_rounded, context=None):
        context = context or {}
        proc_id = super(procurement_order, self)._create_orderpoint_procurement(cr, uid, order_point, qty_rounded, context=context)
        if proc_id:
            bom_obj = self.pool.get('mrp.bom')
            bom_id = bom_obj._bom_find(cr, uid, product_id=order_point.product_id.id, context=context)
            if bom_id:
                uom_obj = self.pool.get('product.uom')
                procurement_obj = self.pool.get('procurement.order')
                proc_point = procurement_obj.browse(cr, uid, proc_id)
                bom_point = bom_obj.browse(cr, uid, bom_id)
                # get components and workcenter_lines from BoM structure
                factor = uom_obj._compute_qty(cr, uid, proc_point.product_uom.id, proc_point.product_qty, bom_point.product_uom.id)
                # product_lines, workcenter_lines (False)
                res = bom_obj._bom_explode(cr, uid, bom_point, proc_point.product_id, factor / bom_point.product_qty, context=context)
                # product_lines
                results = res[0]
                # aa.scheduledate = a.sd - a.produce_delay
                bucket_delay = self._get_bucket_delay(cr, uid, context=context)
                # this 'new' to_date is used for bucket purposes so if weekly buckets in use, will need to line up with preceding bucket tail end
                #context['child_to_date'] = (datetime.strptime(context['to_date'],DEFAULT_SERVER_DATE_FORMAT) + relativedelta(days=bucket_delay) - relativedelta(days=proc_point.product_id.produce_delay)).strftime(DEFAULT_SERVER_DATE_FORMAT)
                context['child_to_date'] = (datetime.strptime(context['to_date'],DEFAULT_SERVER_DATE_FORMAT) - relativedelta(days=proc_point.product_id.produce_delay)).strftime(DEFAULT_SERVER_DATE_FORMAT)
                context['parent_bom_id'] = bom_id
                # process procurements for results
                for product in results:
                    product_obj = self.pool.get('product.product')
                    product_point = product_obj.browse(cr, uid, product['product_id'])
                    proc_id = procurement_obj.create(cr, uid,
                                                    self._prepare_outbound_procurement(cr, uid, product_point, product['product_qty'], product['product_uom'], context=context),
                                                    context=context)
                    self._process_procurement(cr, uid, proc_id, context=context)
                context.pop('child_to_date')
                context.pop('parent_bom_id')

    def _procure_orderpoint_confirm(self, cr, uid, use_new_cursor=False, company_id = False, context=None):
        # delete all procurements matching
        #   created by engine
        #   in confirmed state
        #   not linked to any RFQ or MO
        procurement_obj = self.pool.get('procurement.order')
        dom = [('state','=','confirmed'),('purchase_line_id','=',False),('production_id','=',False),'|',('origin','like','OP/'),('origin','like','OUT/')]
        proc_ids = procurement_obj.search(cr, uid, dom) or []
        if proc_ids:
            procurement_obj.cancel(cr, SUPERUSER_ID, proc_ids, context=context)
            procurement_obj.unlink(cr, SUPERUSER_ID, proc_ids, context=context)
            if use_new_cursor:
                cr.commit()

        super(procurement_order, self)._procure_orderpoint_confirm(cr, uid, use_new_cursor, company_id, context=context)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
