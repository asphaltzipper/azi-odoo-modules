# -*- coding: utf-8 -*-
# See __openerp__.py file for full copyright and licensing details.

from datetime import datetime, timedelta
from openerp import models, fields, api
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, \
    DEFAULT_SERVER_DATE_FORMAT, float_compare, float_round
from psycopg2 import OperationalError
import openerp
import logging
_logger = logging.getLogger(__name__)


class procurement_order(models.Model):
    _inherit = "procurement.order"

    def _get_bucket_size(self, cr, uid, context=None):
        # weekly: 7
        # daily: 1
        return 1 # 1 or preset

    def _get_bucket_delay(self, cr, uid, context=None):
        # subtract relativedelta of days=time_bucket
        # this would need to be handled by a user configurable setting in mfg
        #   if time_bucket=weekly, then we could provide a day of the week for
        #   the user to choose when product should be available and in addition
        #   to the time_bucket, subtract the relative # of days (MON thru SUN)
        #     e.g. MON = -6, - relativedelta(days=6)
        time_bucket = self._get_bucket_size(cr, uid, context=context)
        bucket_day = time_bucket == 7 and 1 or 0 # 1 or preset
        bucket_delay = time_bucket - bucket_day
        return bucket_delay

    def _get_procurement_date_start(self, cr, uid, orderpoint, product_qty, to_date, context=None):
        days = 0.0
        # make addition of lead_days an optional setting
        days += orderpoint.lead_days or 0.0
        product = orderpoint.product_id
        for route in product.route_ids:
            if route.pull_ids:
                for rule in route.pull_ids:
                    if rule.action == 'buy':
                        days += product._select_seller(product, quantity=product_qty, date=to_date, uom_id=orderpoint.product_uom).delay or 0.0
                        days += product.product_tmpl_id.company_id.po_lead
                    if rule.action == 'manufacture':
                        days += product.produce_delay or 0.0
                        days += product.product_tmpl_id.company_id.manufacturing_lead
        #date_start = datetime.combine(datetime.strptime(to_date, DEFAULT_SERVER_DATE_FORMAT) - relativedelta(days=days), datetime.min.time())
        date_start = datetime.strptime(to_date, DEFAULT_SERVER_DATETIME_FORMAT) - relativedelta(days=days)
        return date_start.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    # stock/procurement
    def _prepare_orderpoint_procurement(self, cr, uid, orderpoint, product_qty, context=None):
        res = super(procurement_order, self)._prepare_orderpoint_procurement(cr, uid, orderpoint, product_qty, context=context)
        res['date_planned'] = context['bucket_date']
        return res

    # Method to override in mrp_procurement_only module
    def _process_procurement(self, cr, uid, ids, context=None):
        self.run(cr, uid, ids)

    # Method to override in mrp_procurement_only module
    def _plan_orderpoint_procurement(self, cr, uid, op, qty_rounded, context=None):
        procurement_obj = self.pool.get('procurement.order')
        proc_id = procurement_obj.create(cr, uid,
                                        self._prepare_orderpoint_procurement(cr, uid, op, qty_rounded, context=context),
                                        context=context)
        return proc_id

    @api.model
    def _get_context_dt(self, utc_dt):
        return fields.Datetime.context_timestamp(self, timestamp=utc_dt)

    # override stock/procurement
    def _procure_orderpoint_confirm(self, cr, uid, use_new_cursor=False, company_id = False, context=None):
        '''
        Create procurement based on Orderpoint

        :param bool use_new_cursor: if set, use a dedicated cursor and auto-commit after processing each procurement.
            This is appropriate for batch jobs only.
        '''
        if context is None:
            context = {}
        self._update_llc(cr, uid, use_new_cursor=use_new_cursor, context=context)
        if use_new_cursor:
            cr = openerp.registry(cr.dbname).cursor()
        orderpoint_obj = self.pool.get('stock.warehouse.orderpoint')
        procurement_obj = self.pool.get('procurement.order')
        product_obj = self.pool.get('product.product')

        #TODO:
        # set up time_bucket as mfg cfg setting
        # also need option to choose day of week for procurement
        #   scheduled date when using weekly bucket
        # consider adjusting bucket datetime objects relative to user timezone
        time_bucket = self._get_bucket_size(cr, uid, context=context)
        # get bucket datetime objects
        # as Odoo runs in UTC, datetime.now() is equivalent to datetime.utcnow()
        utc_dt = datetime.combine(datetime.now().date(), datetime.min.time())
        first_bucket_dt = time_bucket == 7 and utc_dt - timedelta(days=utc_dt.weekday()) or utc_dt
        last_bucket_dt = utc_dt
        last_procurement = procurement_obj.search(cr, uid, [('state', '=', 'running')], order="date_planned DESC", limit=1)
        if last_procurement:
            last_procurement_id = last_procurement[0]
            last_bucket_dt = datetime.strptime(procurement_obj.browse(cr, uid, last_procurement_id)['date_planned'], DEFAULT_SERVER_DATETIME_FORMAT)
            last_bucket_dt = time_bucket == 7 and last_bucket_dt + timedelta(days=time_bucket - last_bucket_dt.isoweekday()) or last_bucket_dt
            last_bucket_dt = (last_bucket_dt < first_bucket_dt) and first_bucket_dt or last_bucket_dt
        # get delta from first to last bucket datetime objects
        planning_horizon = (last_bucket_dt - first_bucket_dt).days + time_bucket

        dom = company_id and [('company_id', '=', company_id)] or []
        orderpoint_ids = orderpoint_obj.search(cr, uid, dom, order="location_id, llc")
        prev_ids = []
        tot_procs = []
        while orderpoint_ids:
            ids = orderpoint_ids[:1000]
            del orderpoint_ids[:1000]
            product_dict = {}
            ops_dict = {}
            ops = orderpoint_obj.browse(cr, uid, ids, context=context)

            #Calculate groups that can be executed together
            for op in ops:
                key = (op.location_id.id, op.llc)
                if not product_dict.get(key):
                    product_dict[key] = [op.product_id]
                    ops_dict[key] = [op]
                else:
                    product_dict[key] += [op.product_id]
                    ops_dict[key] += [op]

            for key in sorted(product_dict.keys()):
                plan_days = 0
                while plan_days <= planning_horizon:
                    #to_date = first_bucket_dt.date() + relativedelta(days=plan_days)
                    to_date = first_bucket_dt + relativedelta(days=plan_days)
                    _logger.info("to_date: %s", to_date)

                    ctx = context and context.copy() or {}
                    ctx.update({'location': ops_dict[key][0].location_id.id})
                    #ctx.update({'bucket_date': (to_date - relativedelta(days=self._get_bucket_delay(cr, uid, context=context))).strftime(DEFAULT_SERVER_DATE_FORMAT)})
                    #ctx.update({'bucket_date': (to_date - relativedelta(days=self._get_bucket_delay(cr, uid, context=context))).strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
                    #ctx.update({'bucket_date': (datetime.combine(to_date.date(), datetime.now().time()) - relativedelta(days=self._get_bucket_delay(cr, uid, context=context))).strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
                    # adjust bucket_date relative to user timezone
                    context_hour = self._get_context_dt(cr, uid, context=context, utc_dt=to_date).hour
                    ctx.update({'bucket_date': (to_date + timedelta(hours=context_hour > 12 and 24 - context_hour or 0 - context_hour) - relativedelta(days=self._get_bucket_delay(cr, uid, context=context))).strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
                    ctx.update({'to_date': to_date.strftime(DEFAULT_SERVER_DATE_FORMAT)})
                    ctx.update({'procurement_autorun_defer': True})
                    prod_qty = product_obj._product_available(cr, uid, [x.id for x in product_dict[key]],
                                                            context=ctx)
                    subtract_qty = orderpoint_obj.subtract_procurements_from_orderpoints(cr, uid, [x.id for x in ops_dict[key]], context=ctx)
                    for op in ops_dict[key]:
                        try:
                            prods = prod_qty[op.product_id.id]['virtual_available']
                            _logger.info("op: %s", op)
                            _logger.info("prods: %s", prods)
                            if prods is None:
                                continue
                            if float_compare(prods, op.product_min_qty, precision_rounding=op.product_uom.rounding) <= 0:
                                qty = max(op.product_min_qty, op.product_max_qty) - prods

                                # maintain qty_multiple by subtracting procurements first
                                qty -= subtract_qty[op.id]
                                _logger.info("subtract_qty: %s", subtract_qty[op.id])
                                _logger.info("qty: %s", qty)

                                reste = op.qty_multiple > 0 and qty % op.qty_multiple or 0.0
                                if float_compare(reste, 0.0, precision_rounding=op.product_uom.rounding) > 0:
                                    qty += op.qty_multiple - reste

                                if float_compare(qty, 0.0, precision_rounding=op.product_uom.rounding) < 0:
                                    continue

                                qty_rounded = float_round(qty, precision_rounding=op.product_uom.rounding)
                                if qty_rounded > 0:
                                    ctx.update({'bom_effectivity_date': self._get_procurement_date_start(cr, uid, op, qty_rounded, ctx['bucket_date'], context=ctx)})
                                    proc_id = self._plan_orderpoint_procurement(cr, uid, op, qty_rounded, context=ctx)
                                    tot_procs.extend(proc_id) if isinstance(proc_id, list) else tot_procs.append(proc_id)
                                if use_new_cursor:
                                    cr.commit()
                        except OperationalError:
                            if use_new_cursor:
                                orderpoint_ids.append(op.id)
                                cr.rollback()
                                continue
                            else:
                                raise
                    plan_days = plan_days + time_bucket
            try:
                tot_procs.reverse()
                self._process_procurement(cr, uid, tot_procs, context=context)
                tot_procs = []
                if use_new_cursor:
                    cr.commit()
            except OperationalError:
                if use_new_cursor:
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
