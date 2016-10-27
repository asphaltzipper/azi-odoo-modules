# -*- coding: utf-8 -*-
# © 2016 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, registry
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT, float_compare, float_round
from odoo.osv import expression
from datetime import datetime, timedelta

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

    @property
    def _bucket_size(self):
        # TODO: create bucket_size config parameter
        # daily = 1
        # weekly = 7
        return 7

    @property
    def _merge_back(self):
        # TODO: create merge_back config parameter
        """
        Merge a planned order into a previously planned order, within the lead time for the product.
        Example: A supply order was planned in the previous bucket.  The lead time for this product is 3 weeks.
                 We have found additional demand in the current bucket.  The start date for the new order would fall
                 between the start and finish date of the previous order.  In other words, we would have 2 orders open
                 at the same time.  Rather than create another planned order
                 in this bucket, we may increase the quantity of the previous order.
        """
        return True

    name = fields.Char(
        'Name', copy=False, required=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('mrp.material_plan'))

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        readonly=True,
        required=True)

    default_supplier_id = fields.Many2one(
        comodel_name='res.partner',
        string='Default Vendor',
        ondelete='cascade',
        readonly=True)

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
             'Note that outbound (Demand) orders always have one day delay. i.e. date_start = date_finish - 1.')

    make = fields.Boolean(
        string="Manufacture",
        readonly=True,
        help='This flag is set by the planning algorithm.  '
             'If true, then the algorithm considers dependent demand for any component products, '
             'assuming that an effective BOM was found.')

    orderpoint_id = fields.Many2one(
        comodel_name='stock.warehouse.orderpoint',
        string='Orderpoint',
        readonly=True)

    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location',
        required=True,
        readonly=True,
        help='Location to pass when converting to a procurement order')

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
    def action_convert_to_procurements(self):
        warehouse = self.env['stock.warehouse'].search([], limit=1)
        # TODO: add option to choose day of week for procurement with weekly buckets
        procurement_order = self.env['procurement.order']
        for plan_move in self:
            proc_name = "%s\nuser: %s\nqty: %s\nstart: %s\nfinish: %s" % (
                plan_move.name,
                self.env.user.login,
                plan_move.product_qty,
                plan_move.date_start,
                plan_move.date_finish)
            procurement_order.create(
                {
                    'name': proc_name,
                    'date_planned': plan_move.date_finish,
                    'product_id': plan_move.product_id.id,
                    'product_qty': plan_move.product_qty,
                    'product_uom': plan_move.product_id.uom_id.id,
                    'warehouse_id': plan_move.orderpoint_id.warehouse_id.id if plan_move.orderpoint_id else warehouse[0].id if warehouse else False,
                    'location_id': plan_move.location_id.id,
                    'company_id': plan_move.location_id.company_id.id
                }
            )
            plan_move.unlink()

    def _flag_make_from_procurement_rule(self, location, product):
        """
        Flag this orderpoint as manufactured, based on procurement rule
        We may want to add an interface to the procurement.rule model, so users can change the sequence
        """

        # set domain on locations
        parent_locations = self.env['stock.location']
        child_location = location
        while child_location:
            parent_locations |= child_location
            child_location = child_location.location_id
        domain = [('location_id', 'in', parent_locations.ids)]

        # try finding a rule on product routes
        Pull = self.env['procurement.rule']
        rule = self.env['procurement.rule']
        product_routes = product.route_ids | product.categ_id.total_route_ids
        if product_routes:
            rule = Pull.search(expression.AND([[('route_id', 'in', product_routes.ids)], domain]),
                               order='route_sequence, sequence', limit=1)

        # try finding a rule on warehouse routes
        if not rule:
            warehouse_routes = location.get_warehouse().route_ids
            if warehouse_routes:
                rule = Pull.search(expression.AND([[('route_id', 'in', warehouse_routes.ids)], domain]),
                                   order='route_sequence, sequence', limit=1)

        # try finding a rule that handles orders with no route
        if not rule:
            rule = Pull.search(expression.AND([[('route_id', '=', False)], domain]), order='sequence', limit=1)

        if not rule:
            # TODO: log exception if no rule found
            # if we can't find a rule, try to make it
            _logger.info("No supply rule found for product [%s] %s", product.default_code, product.name)
            import pdb
            pdb.set_trace()
            return True

        if rule.action == 'manufacture':
            return True
        else:
            if rule.action in ('move', 'buy'):
                # move type is not make (no bom explode, no dependent demand)
                return False
            # TODO: log exception if unknown rule found
            _logger.info("Unknown supply rule found for product [%s] %s", product.default_code, product.name)
            # if we get an unknown rule, try to make it
            return True

    def _get_supply_delay_days(self, product, make_flag, product_qty, to_date, orderpoint=None):
        days = 0.0
        # make addition of lead_days an optional setting
        days += orderpoint and orderpoint.lead_days or 0.0
        supplier = self.env['res.partner']
        if make_flag:
            days += product.produce_delay or 0.0
            days += product.product_tmpl_id.company_id.manufacturing_lead
        else:
            supplier = product._select_seller(quantity=product_qty, date=to_date, uom_id=product.uom_id)
            days += supplier.delay or 0.0
            days += product.product_tmpl_id.company_id.po_lead
        return {'days': days, 'supplier_id': supplier and supplier.name.id}

    def _look_backward(self, product_id, bucket_date):
        """
        Merge a planned order into a previously planned order, within the lead time for the product.
        Example: A supply order was planned in the previous bucket.  The lead time for this product is 3 weeks.
                 We have found additional demand in the current bucket.  Rather than create another planned order
                 in this bucket, we may increase the quantity of the previous order.
        :param int product_id:
        :param datetime.date() bucket_date:
        :return self previous_order:
        """
        if not self._merge_back:
            return

        # if product_id == 2064:
        #     import pdb
        #     pdb.set_trace()

        # get previous order
        domain = [('product_id', '=', product_id), ('move_type', '=', 'supply')]
        previous_order = self.search(domain, order='date_finish DESC', limit=1)
        if not previous_order:
            return

        # compare dates
        prev_date_start = datetime.strptime(previous_order.date_start, DEFAULT_SERVER_DATE_FORMAT).date()
        prev_date_finish = datetime.strptime(previous_order.date_finish, DEFAULT_SERVER_DATE_FORMAT).date()
        lead = (prev_date_finish - prev_date_start).days
        new_date_start = bucket_date - timedelta(days=self._bucket_size) - timedelta(days=lead)
        if prev_date_start < new_date_start < prev_date_finish:
            return previous_order

    def _prepare_planned_order(self, product, qty, bucket_date, location, op=None, origin=None, demand=False):
        """
        Prepare a dict of values for creating a material plan record
        :param product.product product:
        :param float qty:
        :param datetime.date() bucket_date:
        :param stock.location location:
        :param stock.warehouse.orderpoint op:
        :param string origin:
        :param bool demand:
        :return dict res:
        """
        move_type = demand and 'demand' or 'supply'
        make_flag = demand and False or self._flag_make_from_procurement_rule(location, product)

        # get supply delay
        date_finish = bucket_date
        date_start = bucket_date
        supply_delay = {}
        if not demand:
            # we are supplying demand for this product sometime in the bucket,
            # but we don't know which day of the bucket, so we assume the worst:
            # set target finish date to the previous bucket boundary
            date_finish -= timedelta(days=self._bucket_size)
            supply_delay = self._get_supply_delay_days(product, make_flag, qty, date_finish, orderpoint=op)
            date_start = date_finish - timedelta(days=supply_delay['days'])
        else:
            # TODO: apply a delay for demand-type moves (from stock to production)
            # we hard-code a delay of one day for moves from stock to production
            date_start -= timedelta(days=1)

        # get name
        name = move_type + "/" + \
            datetime.strftime(date_finish, DEFAULT_SERVER_DATE_FORMAT) + "/" + \
            product.default_code

        res = {
            'name': name,
            'product_id': product.id,
            'default_supplier_id': supply_delay.get('supplier_id'),
            'product_qty': qty,
            'move_type': move_type,
            'make': make_flag,
            'location_id': location.id,
            'orderpoint_id': op and op.id,
            'date_finish': datetime.strftime(date_finish, DEFAULT_SERVER_DATE_FORMAT),
            'date_start': datetime.strftime(date_start, DEFAULT_SERVER_DATE_FORMAT),
            'origin': origin,
        }
        return res

    def _get_orderpoint(self, product, location):
        domain = [('product_id', '=', product.id)]
        parent_locations = self.env['stock.location']
        child_location = location
        while child_location:
            parent_locations |= child_location
            child_location = child_location.location_id
        domain += [('location_id', 'in', parent_locations.ids)]
        return self.env['stock.warehouse.orderpoint'].search(domain, limit=1)

    @api.model
    def _create_dependent_demand(self, additional_qty=None):
        """Explode BOM and create planned orders for dependent demand (outbound, i.e. stock to production)"""
        self.ensure_one()
        if not self.make:
            return

        # explode bom
        bom_id = self.env['mrp.bom']._bom_find(product=self.product_id)
        if not bom_id:
            # TODO: log exception if no bom found
            _logger.info("No BOM found for product [%s] %s", self.product_id.default_code, self.product_id.name)
            return
        product_qty = additional_qty or self.product_qty
        boms, lines = bom_id.explode(self.product_id, product_qty)

        # create dependent demand
        for line, line_data in lines:
            child_op = self._get_orderpoint(line.product_id, self.location_id)
            self.create(
                self._prepare_planned_order(
                    line.product_id,
                    line_data['qty'],
                    datetime.strptime(self.date_start, DEFAULT_SERVER_DATE_FORMAT),
                    self.location_id,
                    op=child_op,
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

    def _get_bucket_from_date(self, str_date=None):
        """
        Returns the date of the next bucket closing boundary after an arbitrary date
        Next Monday for weekly buckets, tomorrow for daily buckets
        The closing boundary date is the date at the end of the bucket
        It is of course also the same as the opening boundary date of the next bucket (if there is a later bucket)
        :param string str_date: arbitrary date string, default=now()
        """
        in_date = datetime.now().date()
        if str_date:
            in_date = datetime.strptime(str_date[0:10], DEFAULT_SERVER_DATE_FORMAT).date()
        if self._bucket_size == 7:
            # use Monday as the boundary
            return in_date - timedelta(days=in_date.weekday()) + timedelta(days=7)
        else:
            return in_date + timedelta(days=self._bucket_size)

    def _get_planning_horizon(self):
        last_bucket_date = self._get_bucket_from_date()

        # get latest stock move
        move_domain = [('state', 'not in', ('done', 'cancel', 'draft'))]
        last_move = self.env['stock.move'].search(move_domain, order="date DESC", limit=1)
        if last_move:
            last_move_date = last_move.date
            last_bucket_date = self._get_bucket_from_date(last_move_date)
        else:
            last_bucket_date += timedelta(days=self._bucket_size)

        # check for a later procurement date
        proc_domain = [('state', '=', 'running')]
        last_proc = self.env['procurement.order'].search(proc_domain, order="date_planned DESC", limit=1)
        last_proc_date = last_proc and datetime.strptime(last_proc.date_planned, DEFAULT_SERVER_DATETIME_FORMAT).date()
        if last_proc and last_proc_date > last_bucket_date:
            last_bucket_date = self._get_bucket_from_date(last_proc.date_planned)

        return last_bucket_date

    def _get_bucket_list(self):
        """Returns a list of bucket closing boundary dates."""
        first_bucket_date = self._get_bucket_from_date()
        last_bucket_date = self._get_planning_horizon()
        if first_bucket_date > last_bucket_date:
            last_bucket_date = first_bucket_date + timedelta(days=self._bucket_size)

        _logger.info(
            'Bucket date range (%s - %s)' %
            (first_bucket_date.strftime(DEFAULT_SERVER_DATE_FORMAT), last_bucket_date.strftime(DEFAULT_SERVER_DATE_FORMAT)))

        # generate list of dates ranging from first bucket date to last bucket date
        bucket_days = int((last_bucket_date - first_bucket_date).days) + 1
        # bucket_list = map(lambda for x: )
        bucket_list = [first_bucket_date + timedelta(days=x) for x in range(0, bucket_days, self._bucket_size)]
        return bucket_list

    @api.model
    def _get_orderpoint_grouping_key(self, orderpoint_ids):
        """Returns tuple of location and llc code"""
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
        # we only retrieve orderpoints for stockable type products
        op_domain = company_id and [('company_id', '=', company_id)] or []
        op_domain += [('product_id.type', '=', 'product')]
        orderpoints_noprefetch = OrderPoint.with_context(prefetch_fields=False).search(
            op_domain,
            order=self.env['procurement.order']._procurement_from_orderpoint_get_order())

        batch_size = 1000
        bucket_count = len(bucket_list)
        op_count = len(orderpoints_noprefetch)
        batch_count = int((op_count+batch_size)/batch_size)
        batch_done = 1

        _logger.info("starting with %d batches and %d buckets" % (batch_count, bucket_count))
        exec_start = time.time()

        while orderpoints_noprefetch:
            orderpoints = OrderPoint.browse(orderpoints_noprefetch[:batch_size].ids)
            orderpoints_noprefetch = orderpoints_noprefetch[batch_size:]

            batch_start = time.time()

            # Calculate groups that can be executed together
            location_data = defaultdict(
                lambda: dict(products=self.env['product.product'], orderpoints=self.env['stock.warehouse.orderpoint']))
            for orderpoint in orderpoints:
                key = self._get_orderpoint_grouping_key([orderpoint.id])
                location_data[key]['products'] += orderpoint.product_id
                location_data[key]['orderpoints'] += orderpoint

            group_count = len(location_data.keys())
            group_done = 1
            for group_key in sorted(location_data.keys()):
                location_orderpoints = location_data[group_key]['orderpoints']
                op_count = len(location_orderpoints)
                product_context = dict(self._context, location=location_orderpoints[0].location_id.id)
                product_quantity = location_data[group_key]['products'].with_context(product_context).bucket_virtual_available(
                    bucket_list, self._bucket_size)
                planned_quantity = location_data[group_key]['products'].bucket_planned_available(bucket_list, self._bucket_size)
                # accumulate planned quantities so we don't have to go to ask the database what we have already planned
                cum_planned = {}

                # TODO: modify subtract_procurements_from_orderpoints to accept to_date in context
                # Should we make subtract_procurements_from_orderpoints() consider to_date in context,
                # or can we pretend that the material supplied by these procurements is available immediately?
                # These procurements represent potential orders that may need to be canceled or expedited.
                # Other systems can report orders that need to be expedited to meet the plan.
                # For now, pretend that the material is available immediately.
                # We may in future eliminate this concept, depending on the origin of said procurements
                subtract_quantity = location_orderpoints.subtract_procurements_from_orderpoints()

                bucket_done = 1

                for bucket_date in bucket_list:
                    op_time = 0
                    check_time = 0
                    create_time = 0
                    new_count = 0
                    exist_count = 0

                    op_done = 1
                    bucket_start = time.time()

                    for orderpoint in location_orderpoints:
                        try:
                            # if orderpoint.product_id.id == 2064:
                            #     import pdb
                            #     pdb.set_trace()
                            local_create_time = 0
                            op_start = time.time()
                            op_product_virtual = product_quantity[(orderpoint.product_id.id, bucket_date)]
                            op_product_virtual += planned_quantity[(orderpoint.product_id.id, bucket_date)]
                            op_product_virtual += cum_planned.get(orderpoint.product_id.id, 0.0)
                            if float_compare(op_product_virtual, orderpoint.product_min_qty,
                                             precision_rounding=orderpoint.product_uom.rounding) <= 0:
                                check_start = time.time()
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
                                    create_start = time.time()
                                    existing_order = self._look_backward(orderpoint.product_id.id, bucket_date)
                                    if existing_order:
                                        existing_order.write({'product_qty': existing_order.product_qty + qty_rounded})
                                        if existing_order.make:
                                            existing_order._create_dependent_demand(qty_rounded)
                                        exist_count += 1
                                        _logger.info("merged order on prod%d" % orderpoint.product_id.id)
                                    else:
                                        new_order = self.create(
                                            self._prepare_planned_order(
                                                orderpoint.product_id,
                                                qty_rounded,
                                                bucket_date,
                                                orderpoint.location_id,
                                                op=orderpoint,
                                                origin=orderpoint.name
                                            )
                                        )
                                        if new_order.make:
                                            new_order._create_dependent_demand()
                                        new_count += 1
                                    cum_planned[orderpoint.product_id.id] = cum_planned.get(orderpoint.product_id.id,
                                                                                            0.0) + qty_rounded
                                    create_stop = time.time()
                                    create_time += create_stop - create_start
                                    local_create_time = create_stop - create_start

                                if use_new_cursor:
                                    cr.commit()

                                create_stop = time.time()
                                check_time += create_stop - check_start

                            op_stop = time.time()
                            op_time += op_stop - op_start
                            # _logger.info(
                            #     "batch=%d/%d "
                            #     "group=%d/%d "
                            #     "bucket=%d/%d "
                            #     "op=%d/%d "
                            #     "op_time=%6.4f "
                            #     "create_time=%6.4f "
                            #     "bucket_date=%s "
                            #     "new=%d "
                            #     "old=%d "
                            #     "op=%d" %
                            #     (
                            #         batch_done,
                            #         batch_count,
                            #         group_done,
                            #         group_count,
                            #         bucket_done,
                            #         bucket_count,
                            #         op_done,
                            #         op_count,
                            #         op_stop - op_start - local_create_time,
                            #         local_create_time,
                            #         bucket_date.strftime(DEFAULT_SERVER_DATE_FORMAT),
                            #         new_count,
                            #         exist_count,
                            #         orderpoint.id
                            #     )
                            # )
                            # op_done += 1

                        except OperationalError:
                            if use_new_cursor:
                                orderpoints_noprefetch += orderpoint.id
                                cr.rollback()
                                continue
                            else:
                                raise

                    bucket_stop = time.time()
                    _logger.info(
                        "batch=%d/%d "
                        "group=%d/%d "
                        "bucket=%d/%d "
                        "bucket_time=%06.4f "
                        "op_time=%06.4f "
                        "check_time=%06.4f "
                        "create_time=%06.4f "
                        "new=%d "
                        "old=%d "
                        "loc=%s "
                        "llc=%s" %
                        (
                            batch_done,
                            batch_count,
                            group_done,
                            group_count,
                            bucket_done,
                            bucket_count,
                            bucket_stop - bucket_start,
                            op_time,
                            check_time,
                            create_time,
                            new_count,
                            exist_count,
                            group_key[0],
                            group_key[1]
                        )
                    )
                    bucket_done += 1

                group_done += 1

            batch_stop = time.time()
            _logger.info("Batch %d/%d execution time=%d" % (batch_count, group_done, batch_stop - batch_start))
            batch_done += 1

        if use_new_cursor:
            cr.commit()
            cr.close()

        exec_stop = time.time()
        _logger.info("plan complete with execution time=%d" % (exec_stop - exec_start))
        return {}
