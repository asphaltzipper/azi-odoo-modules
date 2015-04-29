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
from openerp import models, api
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, \
    DEFAULT_SERVER_DATE_FORMAT, float_compare, float_round
from psycopg2 import OperationalError
import openerp


class procurement_order(models.Model):
    _inherit = "procurement.order"

    def _get_bucket_delay(self, cr, uid, context=None):
        # subtract relativedelta of days=time_bucket
        # this would need to be handled by a user configurable setting in mfg
        #   if time_bucket=weekly, then we could provide a day of the week for
        #   the user to choose when product should be available and in addition
        #   to the time_bucket, subtract the relative # of days (SUN thru SAT)
        #     e.g. MON = -5, - relativedelta(days=5)
        return 1

    def _get_procurement_date_planned(self, cr, uid, to_date, context=None):
        bucket_delay = self._get_bucket_delay(cr, uid, context=context)
        date_planned = datetime.combine(datetime.strptime(to_date,DEFAULT_SERVER_DATE_FORMAT) - relativedelta(days=bucket_delay),datetime.min.time())
        return date_planned.strftime(DEFAULT_SERVER_DATE_FORMAT)

    def _prepare_orderpoint_procurement(self, cr, uid, orderpoint, product_qty, context=None):
        res = super(procurement_order, self)._prepare_orderpoint_procurement(cr, uid, orderpoint, product_qty, context=context)
        res['date_planned'] = self._get_procurement_date_planned(cr, uid, context['to_date'], context=context)
        return res

    def _process_procurement(self, cr, uid, proc_id, context=None):
        self.check(cr, uid, [proc_id])
        self.run(cr, uid, [proc_id])

    def _create_orderpoint_procurement(self, cr, uid, order_point, qty_rounded, context=None):
        procurement_obj = self.pool.get('procurement.order')
        proc_id = procurement_obj.create(cr, uid,
                                        self._prepare_orderpoint_procurement(cr, uid, order_point, qty_rounded, context=context),
                                        context=context)
        self._process_procurement(cr, uid, proc_id, context=context)
        return proc_id
    
    def _product_virtual_get(self, cr, uid, order_point, context=None):
        context = context or {}
        context['location'] = order_point.location_id.id
        product_obj = self.pool.get('product.product')
        return product_obj._product_available(cr, uid,
                [order_point.product_id.id],
                context=context)[order_point.product_id.id]['virtual_available']

    def _procure_orderpoint_confirm(self, cr, uid, use_new_cursor=False, company_id = False, context=None):
        '''
        Create procurement based on Orderpoint
        :param bool use_new_cursor: if set, use a dedicated cursor and auto-commit after processing each procurement.
            This is appropriate for batch jobs only.
        '''
        if context is None:
            context = {}
        if use_new_cursor:
            cr = openerp.registry(cr.dbname).cursor()
        orderpoint_obj = self.pool.get('stock.warehouse.orderpoint')

        #TODO: set up time_bucket as mfg cfg setting
        #      also need option to choose day of week for procurement
        #        scheduled date when using weekly bucket
        #      planning_horizon (first_procurement_dt) should start on a sunday
        #        for weekly bucket
        time_bucket = 1
        procurement_obj = self.pool.get('procurement.order')
        # get earliest date in procurement_order
        first_procurement_id = procurement_obj.search(cr, uid, [('state','=','running')], order="date_planned ASC", limit=1)[0]
        first_procurement_dt = datetime.strptime(procurement_obj.browse(cr, uid, first_procurement_id)['date_planned'], DEFAULT_SERVER_DATETIME_FORMAT)
        # get latest date in procurement_order
        last_procurement_id = procurement_obj.search(cr, uid, [('state','=','running')], order="date_planned DESC", limit=1)[0]
        last_procurement_dt = datetime.strptime(procurement_obj.browse(cr, uid, last_procurement_id)['date_planned'], DEFAULT_SERVER_DATETIME_FORMAT)
        # get delta from first to last procurement 'date_planned'
        planning_horizon = (last_procurement_dt - first_procurement_dt).days + 1

        dom = company_id and [('company_id', '=', company_id)] or []
        orderpoint_ids = orderpoint_obj.search(cr, uid, dom)
        prev_ids = []
        while orderpoint_ids:
            ids = orderpoint_ids[:100]
            del orderpoint_ids[:100]
            for op in orderpoint_obj.browse(cr, uid, ids, context=context):
                try:
                    plan_step = 0
                    while plan_step <= planning_horizon:
                        # set context
                        from_date = first_procurement_dt.date() + relativedelta(days=plan_step)
                        context['to_date'] = (from_date + relativedelta(days=time_bucket)).strftime(DEFAULT_SERVER_DATE_FORMAT)

                        prods = self._product_virtual_get(cr, uid, op, context=context)
                        if prods is None:
                            continue
                        if float_compare(prods, op.product_min_qty, precision_rounding=op.product_uom.rounding) < 0:
                            qty = max(op.product_min_qty, op.product_max_qty) - prods
                            reste = op.qty_multiple > 0 and qty % op.qty_multiple or 0.0
                            if float_compare(reste, 0.0, precision_rounding=op.product_uom.rounding) > 0:
                                qty += op.qty_multiple - reste

                            if float_compare(qty, 0.0, precision_rounding=op.product_uom.rounding) <= 0:
                                continue

                            qty -= orderpoint_obj.subtract_procurements(cr, uid, op, context=context)

                            qty_rounded = float_round(qty, precision_rounding=op.product_uom.rounding)
                            if qty_rounded > 0:
                                self._create_orderpoint_procurement(cr, uid, op, qty_rounded, context=context)
                        plan_step = plan_step + time_bucket
                    if use_new_cursor:
                        cr.commit()
                except OperationalError:
                    if use_new_cursor:
                        orderpoint_ids.append(op.id)
                        cr.rollback()
                        continue
                    else:
                        raise
            if use_new_cursor:
                cr.commit()
            if prev_ids == ids:
                break
            else:
                prev_ids = ids

        if use_new_cursor:
            cr.commit()
            cr.close()
        return {}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
