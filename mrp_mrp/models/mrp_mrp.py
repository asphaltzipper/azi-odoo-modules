# -*- coding: utf-8 -*-
# © 2016 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, registry
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT, float_compare, float_round
from odoo.osv import expression
from datetime import datetime, timedelta
# from dateutil.relativedelta import relativedelta

from collections import defaultdict
from psycopg2 import OperationalError

import odoo.addons.decimal_precision as dp

import time
import logging
_logger = logging.getLogger(__name__)

class MrpMaterialPlan(models.Model):
    """
        Calculate and manage material requirements plan data, per MRP standards.
        We will implement an efficient mrp algorithm, similar to _procure_orderpoint_confirm().
        Since this is MRP-1, it has all the usual problems of MRP:
            - infinite capacity assumption
            - zero delay for internal moves
            - data integrity (garbage in, garbage out)
            - nervousness
            - bullwhip effect
        But, it fixes the problems with the standard Odoo scheduler:
            - low-level coding
            - time phasing / buckets
            - plan modification
    """

    _name = "mrp.material_plan"
    _description = "Plan Material Moves"

    name = fields.Char(
        'Name', copy=False, required=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('mrp.material_plan'))

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        readonly=True,
        required=True)

    product_qty = fields.Float(
        string='Quantity',
        digits=dp.get_precision('Product Unit of Measure'),
        readonly=True,
        required=True)

    move_type = fields.Selection(
        selection=[('supply', 'Supply'), ('demand', 'Demand')],
        string='Move Type',
        required=True,
        readonly=True,
        help='Direction of planned material flow for this order:\n'
             ' - Supply: vendor/production -> stock\n'
             ' - Demand: stock -> production\n'
             'Note that outbound (Demand) orders always have delay of one day.')

    make = fields.Boolean(
        string="Manufacture",
        readonly=True,
        help='This flag is set by the planning algorithm.  '
             'If true, then the algorithm considers dependent demand for any component products, '
             'assuming that an effective BOM was found.')

    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        readonly=True,
        help='Warehouse to pass to the procurement order')

    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location',
        readonly=True,
        help='Location to pass to the procurement order')

    date_finish = fields.Date(
        string='Finish Date',
        required=True,
        readonly=True,
        index=True,
        track_visibility='onchange',
        help='Planned date of completion for this order.  '
             'For purchased products, this is the date of delivery from vendor.  '
             'For manufactured products, this is the date the product is moved from production to stock.')

    date_start = fields.Date(
        string='Start Date',
        required=False,
        index=True,
        select=True,
        readonly=True,
        help='Start date of this order.  Calculated as the planned date of completion (Finish Date) minus the lead '
             'time for this product.')

    origin = fields.Char(
        string='Demand Origin',
        help="Reference of the Supply/Make order that consumes this Demand/Move order.")

    @api.multi
    def convert_to_procurements(self):
        # TODO: add option to choose day of week/month for procurement with weekly/monthly buckets
        procurement_order = self.env['procurement.order']
        for plan_move in self:
            procurement_order.create({
                'name': '%s\nuser: %s\nqty: %s\nstart: %s\nfinish: %s' % (
                    plan_move.name, self.env.user.login, plan_move.product_qty, plan_move.date_start,
                    plan_move.date_finish),
                'date_planned': plan_move.date_finish,
                'product_id': plan_move.product_id.id,
                'product_qty': plan_move.product_qty,
                'product_uom': plan_move.product_id.uom_id.id,
                'warehouse_id': plan_move.warehouse_id.id,
                'location_id': plan_move.warehouse_id.lot_stock_id.id,
                'company_id': plan_move.warehouse_id.company_id.id})
            plan_move.unlink()

    def _flag_make_from_procurement_rule(self, op):
        """
        Flag this orderpoint as manufactured, based on procurement rule
        We may want to add an interface to the procurement.rule model, so users can change the sequence
        """

        # set domain on locations
        parent_locations = self.env['stock.location']
        location = op.location_id
        while location:
            parent_locations |= location
            location = location.location_id
        domain = [('location_id', 'in', parent_locations.ids)]

        # try finding a rule on product routes
        Pull = self.env['procurement.rule']
        rule = self.env['procurement.rule']
        product_routes = op.product_id.route_ids | self.product_id.categ_id.total_route_ids
        if product_routes:
            rule = Pull.search(expression.AND([[('route_id', 'in', product_routes.ids)], domain]),
                               order='route_sequence, sequence', limit=1)

        # try finding a rule on warehouse routes
        if not rule:
            warehouse_routes = op.location_id.get_warehouse().route_ids
            if warehouse_routes:
                rule = Pull.search(expression.AND([[('route_id', 'in', warehouse_routes.ids)], domain]),
                                   order='route_sequence, sequence', limit=1)

        # try finding a rule that handles orders with no route
        if not rule:
            rule = Pull.search(expression.AND([[('route_id', '=', False)], domain]), order='sequence', limit=1)

        if not rule:
            # TODO: log exception if no rule found
            # if we can't find a rule, try to make it
            return True

        if rule.action == 'manufacture':
            return True
        else:
            if rule.action in ('move', 'buy'):
                # move type is not make (no bom explode, no dependent demand)
                return False
            # TODO: log exception if unknown rule found
            # if we get an unknown rule, try to make it
            return True

    def _get_supply_delay_days(self, orderpoint, make_flag, product_qty, to_date):
        days = 0.0
        # make addition of lead_days an optional setting
        days += orderpoint.lead_days or 0.0
        if make_flag:
            days += orderpoint.product_id.produce_delay or 0.0
            days += orderpoint.product_id.product_tmpl_id.company_id.manufacturing_lead
        else:
            days += orderpoint.product_id._select_seller(quantity=product_qty, date=to_date,
                                                         uom_id=orderpoint.product_uom).delay or 0.0
            days += orderpoint.product_id.product_tmpl_id.company_id.po_lead
        return days

    def _look_backward(self, product_id, bucket_date):
        """
        Merge a planned order into a previously planned order, within the lead time for the product.
        Example: A supply order was planned in the previous bucket.  The lead time for this product is 3 weeks.
                 We have found additional demand in the current bucket.  Rather than create another planned order
                 in this bucket, we may increase the quantity of the previous order.
        :param product_id:
        :param bucket_date:
        :return previous_order:
        """
        # TODO: create merge_back config parameter
        # get merge_back config parameter
        merge_back = True
        if not merge_back:
            return

        # get previous order
        domain = [('product_id', '=', product_id), ('date_start', '<', bucket_date), ('date_finish', '>', bucket_date)]
        previous_order = self.search(domain, order='date_finish DESC', limit=1)
        if not previous_order:
            return

        # compare dates
        prev_date_start = previous_order.date_start
        prev_date_finish = previous_order.date_finish
        lead = previous_order.date_finish - previous_order.date_start
        new_date_start = bucket_date - timedelta(days=lead)
        if prev_date_start < new_date_start < prev_date_finish:
            return previous_order

    def _prepare_planned_order(self, product, qty, bucket_date, op=None, origin=None, demand=False):

        move_type = demand and 'demand' or 'supply'

        make_flag = None
        if not demand:
            make_flag = self._flag_make_from_procurement_rule(op)

        # get supply delay
        date_finish = bucket_date
        date_start = bucket_date
        if demand:
            # TODO: provide a setting parameter for delay of demand-type moves (from stock to production)
            # we hard-code a delay of one day for moves from stock to production
            date_start -= timedelta(days=1)
        else:
            # we are supplying demand for this product sometime in the bucket,
            # but we don't know which day of the bucket, so we assume the worst:
            # set target finish date to the previous bucket date
            date_finish -= timedelta(days=self.BucketSize())
            date_start = date_finish - timedelta(days=self._get_supply_delay_days(op, make_flag, qty, date_finish))

        # get warehouse
        warehouse_id = op and op.location_id.get_warehouse().id or None

        # get name
        name = move_type + "/" + \
            datetime.strftime(date_finish, DEFAULT_SERVER_DATE_FORMAT) + "/" + \
            product.default_code

        res = {
            'name': name,
            'product_id': product.id,
            'product_qty': qty,
            'move_type': move_type,
            'make': make_flag,
            'warehouse_id': warehouse_id,
            'date_finish': datetime.strftime(date_finish, DEFAULT_SERVER_DATE_FORMAT),
            'date_start': datetime.strftime(date_start, DEFAULT_SERVER_DATE_FORMAT),
            'origin': origin,
        }
        return res

    @api.model
    def _create_dependent_demand(self, op=None):
        """Explode BOM and create planned orders for dependent demand (outbound, i.e. stock to production)"""
        self.ensure_one()
        bom_id = self.env['mrp.bom']._bom_find(product=self.product_id)
        if not bom_id:
            # TODO: log exception if no bom found
            return
        boms, lines = bom_id.explode(self.product_id, self.product_qty)
        for line, line_data in lines:
            # TODO: log exception if no orderpoint exists for bom line item
            self.create(
                self._prepare_planned_order(
                    line.product_id,
                    line_data['qty'],
                    datetime.strptime(self.date_start, DEFAULT_SERVER_DATE_FORMAT),
                    op=op,
                    origin=self.name,
                    demand=True
                )
            )

    @api.model
    def purge_old_plan(self):
        # delete all planned moves
        records = self.search([])
        _logger.info("Deleting %s planned moves", len(records))
        records.unlink()

    def _get_bucket_size(self):
        # TODO: set up time_bucket as mfg cfg setting
        # daily = 1
        # weekly = 7
        # TODO: add handling for monthly buckets
        return 1

    BucketSize = _get_bucket_size

    def _get_bucket_from_date(self, str_date=None):
        """
        Returns the date of the next bucket closing boundary after an arbitrary date
        Next Monday for weekly buckets, tomorrow for daily buckets
        The closing boundary date is the date at the end of the bucket
        It is of course also the same as the opening boundary date of the next bucket (if there is a later bucket)
        :param string str_date: arbitrary date string, default=now()
        """
        if not str_date:
            return datetime.now().date() + timedelta(days=self.BucketSize())

        in_date = datetime.strptime(str_date[0:10], DEFAULT_SERVER_DATE_FORMAT).date()
        # TODO: add handling for monthly buckets
        if self.BucketSize() == 7:
            # We always use Monday as the boundary because that's how PostgreSQL truncates dates by week
            return in_date - timedelta(days=in_date.weekday()) + timedelta(days=7)
        else:
            return in_date + timedelta(days=self.BucketSize())

    def _get_bucket_list(self):
        """
        Returns a list of bucket closing boundary dates.
        Closing boundary dates correspond with the to_date context variable
        """
        first_bucket_dt = self._get_bucket_from_date()
        last_bucket_dt = first_bucket_dt

        # get last procurement date
        last_proc = self.env['procurement.order'].search([('state', '=', 'running')], order="date_planned DESC", limit=1)
        if last_proc:
            last_proc_date = last_proc.date_planned
            last_bucket_dt = self._get_bucket_from_date(last_proc_date)
        else:
            last_bucket_dt += timedelta(days=self.BucketSize())

        _logger.info(
            'Bucket date range (%s - %s)' %
            (first_bucket_dt.strftime(DEFAULT_SERVER_DATE_FORMAT), last_bucket_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)))

        # generate list of dates ranging from first bucket date to last bucket date
        bucket_days = int((last_bucket_dt - first_bucket_dt).days) + 1
        # bucket_list = map(lambda for x: )
        bucket_list = [first_bucket_dt + timedelta(days=x) for x in range(0, bucket_days, self.BucketSize())]
        return bucket_list

    @api.model
    def _get_orderpoint_grouping_key(self, orderpoint_ids):
        orderpoints = self.env['stock.warehouse.orderpoint'].browse(orderpoint_ids)
        return orderpoints.location_id.id, orderpoints.llc

    @api.model
    def _run_mrp_api(self, use_new_cursor=False, company_id=False):
        """ Create planned orders based on orderpoints.
        :param bool use_new_cursor: if set, use a dedicated cursor and auto-commit after processing each procurement.
            This is appropriate for batch jobs only.
        """
        if use_new_cursor:
            cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=cr))

        # delete old plan
        self.purge_old_plan()

        bucket_list = self._get_bucket_list()

        OrderPoint = self.env['stock.warehouse.orderpoint']

        # this algorithm assumes the mrp_llc module updates and sorts on low-level-code
        orderpoints_noprefetch = OrderPoint.with_context(prefetch_fields=False).search(
            company_id and [('company_id', '=', company_id)] or [],
            order=self.env['procurement.order']._procurement_from_orderpoint_get_order())

        bucket_count = len(bucket_list)
        # bucket_done = 1
        op_count = len(orderpoints_noprefetch)
        batch_count = int((op_count+1000)/1000)
        # batch_done = 1

        _logger.info("starting with %d batches and %d buckets" % (batch_count, bucket_count))
        ops_exec_start = time.time()

        while orderpoints_noprefetch:
            orderpoints = OrderPoint.browse(orderpoints_noprefetch[:1000].ids)
            orderpoints_noprefetch = orderpoints_noprefetch[1000:]

            # Calculate groups that can be executed together
            location_data = defaultdict(
                lambda: dict(products=self.env['product.product'], orderpoints=self.env['stock.warehouse.orderpoint'],
                             groups=list()))
            for orderpoint in orderpoints:
                key = self._get_orderpoint_grouping_key([orderpoint.id])
                location_data[key]['products'] += orderpoint.product_id
                location_data[key]['orderpoints'] += orderpoint

            for location_id, location_data in location_data.iteritems():
                location_orderpoints = location_data['orderpoints']
                product_context = dict(self._context, location=location_orderpoints[0].location_id.id)
                product_quantity = location_data['products'].with_context(product_context).bucket_virtual_available(
                    bucket_list, self.BucketSize())

                # TODO: modify subtract_procurements_from_orderpoints to accept to_date in context
                # Should we make subtract_procurements_from_orderpoints() consider to_date in context,
                # or can we pretend that the material supplied by these procurements is available immediately?
                # These procurements represent potential orders that may need to be canceled or expedited.
                # Other systems can report orders that need to be expedited to meet the plan.
                # For now, pretend that the material is available immediately.
                # We may in future eliminate this concept, depending on the origin of said procurements
                subtract_quantity = location_orderpoints.subtract_procurements_from_orderpoints()

                for bucket_date in bucket_list:
                    planned_quantity = location_data['products'].planned_virtual_available(bucket_date)

                    for orderpoint in location_orderpoints:
                        try:
                            key = (orderpoint.product_id.id, bucket_date)
                            if not key in product_quantity.keys():
                                import pdb
                                pdb.set_trace()
                            op_product_virtual = product_quantity[key]
                            if op_product_virtual is None:
                                continue
                            op_product_virtual += planned_quantity[orderpoint.product_id.id]
                            if float_compare(op_product_virtual, orderpoint.product_min_qty,
                                             precision_rounding=orderpoint.product_uom.rounding) <= 0:
                                qty = max(orderpoint.product_min_qty, orderpoint.product_max_qty) - op_product_virtual

                                # maintain qty_multiple by subtracting procurements first
                                qty -= subtract_quantity[orderpoint.id]

                                remainder = orderpoint.qty_multiple > 0 and qty % orderpoint.qty_multiple or 0.0

                                if float_compare(remainder, 0.0, precision_rounding=orderpoint.product_uom.rounding) > 0:
                                    qty += orderpoint.qty_multiple - remainder

                                if float_compare(qty, 0.0, precision_rounding=orderpoint.product_uom.rounding) < 0:
                                    continue

                                qty_rounded = float_round(qty, precision_rounding=orderpoint.product_uom.rounding)
                                if qty_rounded > 0:
                                    existing_order = self._look_backward(orderpoint.product_id.id, bucket_date)
                                    if existing_order:
                                        existing_order.write({'product_qty': existing_order.product_qty + qty_rounded})
                                        if existing_order.make:
                                            existing_order._create_dependent_demand(orderpoint)
                                    else:
                                        new_order = self.create(
                                            self._prepare_planned_order(
                                                orderpoint.product_id,
                                                qty_rounded,
                                                bucket_date,
                                                op=orderpoint,
                                                origin=orderpoint
                                            )
                                        )
                                        if new_order.make:
                                            new_order._create_dependent_demand(orderpoint)

                                if use_new_cursor:
                                    cr.commit()

                        except OperationalError:
                            if use_new_cursor:
                                orderpoints_noprefetch += orderpoint.id
                                cr.rollback()
                                continue
                            else:
                                raise

        if use_new_cursor:
            cr.commit()
            cr.close()
        return {}

        ops_exec_stop = time.time()
        _logger.info("create=%d" % (ops_exec_stop - ops_exec_start))




















# ##############################################################################

def _get_orderpoints(self):
    # get cumulative inventory state by orderpoint
    self._cr.execute("""
        -- procurement quantities (confirmed, exception, running)
        -- later, subtract without a stock move
        SELECT
            orderpoint.id,
            procurement.id,
            procurement.product_uom,
            procurement.product_qty,
            template.uom_id,
            move.product_qty
        FROM stock_warehouse_orderpoint AS orderpoint
        JOIN procurement_order AS procurement ON procurement.orderpoint_id = orderpoint.id
        JOIN product_product AS product ON product.id = procurement.product_id
        JOIN product_template AS template ON template.id = product.product_tmpl_id
        LEFT JOIN stock_move AS move ON move.procurement_id = procurement.id
        WHERE procurement.state not in ('done', 'cancel')
        AND (move.state IS NULL OR move.state != 'draft')
        AND p.date_planned <= %s
        ORDER BY orderpoint.id, procurement.id
    """)

    # quantity of product that needs to be added to the inventory state because there's a procurement existing with
    # aim to supply it, less associated stock moves that have already been created
    # procurements associated to an orderpoint
    # state in (confirmed, exception, running)
    self._cr.execute("""
        -- procurement quantities (confirmed, exception, running)
        -- later, subtract without a stock move
        SELECT
            orderpoint.id,
            procurement.id,
            procurement.product_uom,
            procurement.product_qty / uom.factor as product_qty,
            template.uom_id,
            move.product_qty
        FROM stock_warehouse_orderpoint AS orderpoint
        JOIN procurement_order AS procurement ON procurement.orderpoint_id = orderpoint.id
        JOIN product_product AS product ON product.id = procurement.product_id
        JOIN product_template AS template ON template.id = product.product_tmpl_id
        LEFT JOIN stock_move AS move ON move.procurement_id = procurement.id
        left join product_uom as uom on uom.id=procurement.product_uom
        WHERE procurement.state not in ('done', 'cancel')
        AND (move.state IS NULL OR move.state != 'draft')
        ORDER BY orderpoint.id, procurement.id
    """)

    # add procurement supply to inventory state


@api.model
def run_mrp_db(self):
    # mrp algorithm to calculate requirements

    ProcOrder = self.env['procurement.order']

    # delete old plan
    self.purge_old_plan()

    # get buckets
    bucket_list = self._get_bucket_list()

    # get orderpoints by llc
    op_list = self._get_orderpoints()
    OrderPoint = self.env['stock.warehouse.orderpoint']
    orderpoints_noprefetch = OrderPoint.with_context(prefetch_fields=False).search(
        order=ProcOrder._procurement_from_orderpoint_get_order())

    move_list = []

    # get default leadtime and route for orderpoint products
    # crit = {
    #     'X000001.-0': {
    #         'leadtime': 1,
    #         'route': 'make',
    #     }
    # }

    # build data matrix container
    # data = {
    #     '2017-01-01': {
    #         'X000001.-0': {},
    #         'X000002.-0': {},
    #         ...
    #     },
    #     '2017-01-02': {
    #         'X000001.-0': {},
    #         'X000002.-0': {},
    #         ...
    #     }
    #     ...
    # }

    # add detail dict at each cell
    # data['2017-01-01']['X000001.-0'] = {
    #     'real_state': 0,
    #     'cumulative_plan': 0,
    #     'activity': 0,
    # }

    # loop low-level codes
    while orderpoints_noprefetch:
        orderpoints = OrderPoint.browse(orderpoints_noprefetch[:1000].ids)
        orderpoints_noprefetch = orderpoints_noprefetch[1000:]

        # loop orderpoints

        # loop buckets

        # get inventory state at bucket date

        # add supply activity (positive/inbound)

        # if route == make

        # explode bom

        # subtract demand activity (negative/outbound)
        # report exception when products with dependent demand have no reorder rule

    # write new plan

    pass

