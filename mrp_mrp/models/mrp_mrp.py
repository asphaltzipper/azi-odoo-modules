# -*- coding: utf-8 -*-
# © 2016 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api
import odoo.addons.decimal_precision as dp


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
    _description = "Plan Material Data"

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
        help='Supply route that was assumed in planned this order.')

    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        required=True,
        readonly=True,
        help='Warehouse to consider for the route selection')

    date_finish = fields.Datetime(
        string='Finish Date',
        required=True,
        readonly=True,
        index=True,
        track_visibility='onchange',
        help='Planned date of completion for this order.  '
             'For purchased products, this is the date of delivery from vendor.  '
             'For manufactured products, this is the date the product is moved from production to stock.')

    date_start = fields.Datetime(
        string='Start Date',
        required=False,
        index=True,
        select=True,
        readonly=True,
        help='Start date of this order.  Calculated as the planned date of completion (Finish Date) minus the lead '
             'time for this product.')


    @api.model
    def run_mrp(self):
        # mrp algorithm to calculate requirements

        # delete old plan

        # get buckets

        # get orderpoints by llc

        # build planned inventory activity matrix (start with all zeros)
        # a = {
        #     '2017-01-01': {
        #         'X000001.-0': 0,
        #         'X000002.-0': 0,
        #         ...
        #     },
        #     '2017-01-02': {
        #         'X000001.-0': 0,
        #         'X000002.-0': 0,
        #         ...
        #     }
        #     ...
        # }

        # build real inventory state matrix (copy from above and populate with sql query)
        # s = a.copy()

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
