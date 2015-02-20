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
from openerp import models, api, SUPERUSER_ID
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, \
    DEFAULT_SERVER_DATE_FORMAT, float_compare, float_round
from psycopg2 import OperationalError
import openerp


class procurement_order(models.Model):
    _inherit = "procurement.order"

    def run_scheduler(self, cr, uid, use_new_cursor=False, company_id=False, context=None):
        '''
        Call the scheduler in order to check the running procurements (replace built-in run_scheduler to eliminate the
        running of confirmed procurements), to check the minimum stock rules and the availability of moves. This 
        function is intended to be run for all the companies at the same time, so we run functions as SUPERUSER to 
        avoid intercompanies and access rights issues.
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

    def _prepare_orderpoint_procurement(self, cr, uid, orderpoint, product_qty, context=None):
        res = super(procurement_order, self)._prepare_orderpoint_procurement(cr, uid, orderpoint, product_qty, context=context)
        if 'push_forward' in context and context['push_forward']==0:
            # set location
            #res['location_id'] = 
            import pdb
            pdb.set_trace()
        return res

    def _process_orderpoint_procurement(self, cr, uid, proc_id, context=None):
        self.check(cr, uid, [proc_id])
        #self.run(cr, uid, [proc_id])

    def _create_orderpoint_procurement(self, cr, uid, order_point, qty_rounded, context=None):
        context = context or {}
        proc_id = super(procurement_order, self)._create_orderpoint_procurement(cr, uid, order_point, qty_rounded, context=context)
        # push forward
        # _bom_explode on orderpoint.product_id children if bom_id
        # aa.scheduledate = a.sd-a.produce_delay
        #import pdb
        #pdb.set_trace()
        #if proc_id and not context['push_forward']==0:
        if proc_id and 'push_forward' not in context:
            bom_obj = self.pool.get('mrp.bom')
            bom_id = bom_obj._bom_find(cr, uid, product_id=order_point.product_id.id, context=context)
            if bom_id:
                #res = prod_obj._prepare_lines(cr, uid, bom_obj.browse(cr, uid, bom_id, context=context), context=context)
                uom_obj = self.pool.get('product.uom')
                proc_obj = self.pool.get('procurement.order')
                proc_point = proc_obj.browse(cr, uid, proc_id)
                bom_point = bom_obj.browse(cr, uid, bom_id)
                # get components and workcenter_lines from BoM structure
                factor = uom_obj._compute_qty(cr, uid, proc_point.product_uom.id, proc_point.product_qty, bom_point.product_uom.id)
                # product_lines, workcenter_lines (False)
                res = bom_obj._bom_explode(cr, uid, bom_point, proc_point.product_id, factor / bom_point.product_qty, context=context)
                # product_lines
                results = res[0]
                context['push_forward'] = 0
                import pdb
                pdb.set_trace()
                context['to_date'] = (datetime.strptime(context['to_date'],DEFAULT_SERVER_DATE_FORMAT) - relativedelta(days=proc_point.product_id.produce_delay)).strftime(DEFAULT_SERVER_DATE_FORMAT)
                orderpoint_obj = self.pool.get('stock.warehouse.orderpoint')
                # process procurements for results
                for prod in results:
                    dom = prod['product_id'] and [('product_id', '=', prod['product_id'])] or []
                    orderpoint_ids = orderpoint_obj.search(cr, uid, dom)
                    # potential issue if more than one orderpoint per product
                    #   procurement order could be created for each orderpoint
                    for op in orderpoint_obj.browse(cr, uid, orderpoint_ids, context=context):
                        self._try_orderpoint_procurement(cr, uid, op, prod, context=context)

    def _procure_orderpoint_confirm(self, cr, uid, use_new_cursor=False, company_id = False, context=None):
        # delete all procurements matching
        #   created by engine
        #   in confirmed state
        #   not linking to any RFQ or MO
        proc_obj = self.pool.get('procurement.order')
        dom = [('origin','like','OP/'),('state','=','confirmed'),('purchase_line_id','=',False),('production_id','=',False)]
        proc_ids = proc_obj.search(cr, uid, dom) or []
        import pdb
        pdb.set_trace()
        if proc_ids:
            proc_obj.cancel(cr, SUPERUSER_ID, proc_ids, context=context)
            proc_obj.unlink(cr, SUPERUSER_ID, proc_ids, context=context)
            if use_new_cursor:
                cr.commit()

        super(procurement_order, self)._procure_orderpoint_confirm(cr, uid, use_new_cursor, company_id, context=context)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
