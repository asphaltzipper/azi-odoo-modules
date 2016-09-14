# -*- coding: utf-8 -*-
# © 2016 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api
import odoo.addons.decimal_precision as dp
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT, float_compare, float_round
from datetime import datetime, timedelta
# from dateutil.relativedelta import relativedelta

import logging
_logger = logging.getLogger(__name__)

class MrpMaterialPlan(models.Model):
    """
        Calculate and manage material requirements plan data, per MRP standards.
        We will implement an efficient mrp algorithm.
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
             'Note that outbound (Demand) orders will have the start and finish dates equal.  '
             'This implies that moving material from stock to production has no delay.')

    route = fields.Selection(
        selection=[('make', 'Make'), ('buy', 'Buy'), ('move', 'Move')],
        string="Supply Route",
        track_visibility='onchange',
        help='Supply route that was assumed in planning this order.')

    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        required=True,
        readonly=True,
        help='Warehouse to consider for the route selection')

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
        help="Reference of the Supply/Make order that has consumes this Demand/Move order.")

    @api.model
    def purge_old_plan(self):
        # delete all planned moves
        _logger.info("Deleting %s planned moves", len(self))
        self.search([]).unlink()
        _logger.info("Done deleting")

    def _get_bucket_size(self):
        # TODO: set up time_bucket as mfg cfg setting
        # daily = 1
        # weekly = 7
        # TODO: add capability for monthly buckets
        return 1

    BucketSize = _get_bucket_size()

    def _get_bucket_from_date(self, str_date=None):
        # as Odoo runs in UTC, datetime.now() is equivalent to datetime.utcnow()
        in_date = str_date and datetime.strptime(str_date, DEFAULT_SERVER_DATE_FORMAT) or datetime.now().date()
        # TODO: add handling for monthly buckets
        return self.BucketSize == 7 and in_date - timedelta(days=in_date.weekday()) or in_date

    def _get_bucket_list(self):
        # TODO: add option to choose day of week/month for procurement
        first_bucket_dt = self._get_bucket_from_date()
        last_bucket_dt = first_bucket_dt

        # get last procurement date
        ProcurementOrder = self.env['procurement.order']
        last_procurement = ProcurementOrder.search([('state', '=', 'running')], order="date_planned DESC", limit=1)
        if last_procurement:
            last_procurement_id = last_procurement[0]
            last_proc_date = ProcurementOrder.browse(last_procurement_id)['date_planned']
            last_bucket_dt = self._get_bucket_from_date(last_proc_date)

        # generate list of dates ranging from first bucket date to last bucket date
        bucket_list = [last_bucket_dt + datetime.timedelta(days=x) for x in range(0, self.BucketSize)]
        return bucket_list

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
    def run_mrp(self):
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

            # loop buckets

                # get inventory state at bucket date

                # loop orderpoints

                    # add supply activity (positive/inbound)

                    # if route == make

                        # explode bom

                        # subtract demand activity (negative/outbound)
                        # report exception when products with dependent demand have no reorder rule

        # write new plan

        pass


@api.multi
def convert_to_procurements(self):
    procurement_order = self.env['procurement.order']
    for plan_move in self:
        procurement_order.create({
            'name': '%s\nuser: %s\nqty: %s\nstart: %s\nfinish: %s' % (
            plan_move.name, self.env.user.login, plan_move.product_qty, plan_move.date_start, plan_move.date_finish),
            'date_planned': plan_move.date_finish,
            'product_id': plan_move.product_id.id,
            'product_qty': plan_move.product_qty,
            'product_uom': plan_move.product_id.uom_id.id,
            'warehouse_id': plan_move.warehouse_id.id,
            'location_id': plan_move.warehouse_id.lot_stock_id.id,
            'company_id': plan_move.warehouse_id.company_id.id})
        plan_move.unlink()

