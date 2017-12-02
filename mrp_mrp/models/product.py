# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, float_round
from odoo.exceptions import UserError
from odoo.osv import expression


class Product(models.Model):
    _inherit = "product.product"

    @api.multi
    def planned_qty(self, to_date=None):
        """Return planned net move quantity, for select products, through the given date"""

        # build domain for searching mrp.material_plan records
        domain = [('product_id', 'in', self.ids)]
        if to_date:
            domain += [('date_finish', '<', to_date)]
        domain_in = domain + [('move_type', '=', 'supply')]
        domain_out = domain + [('move_type', '=', 'demand')]

        # get moves
        MrpPlan = self.env['mrp.material_plan']
        moves_in = dict((item['product_id'][0], item['product_qty']) for item in
                        MrpPlan.read_group(domain_in, ['product_id', 'product_qty'], ['product_id']))
        moves_out = dict((item['product_id'][0], item['product_qty']) for item in
                         MrpPlan.read_group(domain_out, ['product_id', 'product_qty'], ['product_id']))

        # return dict
        res = dict()
        for product in self.with_context(prefetch_fields=False):
            qty_in = float_round(moves_in.get(product.id, 0.0), precision_rounding=product.uom_id.rounding)
            qty_out = float_round(moves_out.get(product.id, 0.0), precision_rounding=product.uom_id.rounding)
            res[product.id] = {
                'qty_in': qty_in,
                'qty_out': qty_out,
                'qty_net': float_round(qty_in - qty_out, precision_rounding=product.uom_id.rounding),
            }
        return res

    @api.multi
    def bucket_planned_qty(self, bucket_list, bucket_size):
        """Return cumulative planned net move quantity, for select products, grouped by bucket date"""

        # if 13964 in self.ids:
        #     import pdb
        #     pdb.set_trace()

        if bucket_list[0] < datetime.now().date():
            raise UserError(_('The beginning bucket date is in the past.  All bucket dates must be in the future.'))
        date_group_out = bucket_size == 7 and 'date_start:week' or 'date_start:day'
        date_group_in = bucket_size == 7 and 'date_finish:week' or 'date_finish:day'
        init_date = bucket_list[0].strftime(DEFAULT_SERVER_DATE_FORMAT)

        # build domain for searching mrp.material_plan records
        domain = [('product_id', 'in', self.ids)]
        domain_in = domain + [('move_type', '=', 'supply')]
        domain_out = domain + [('move_type', '=', 'demand')]

        # get planned moves up to the initial bucket date
        MrpPlan = self.env['mrp.material_plan']
        moves_in_init = dict(
            (item['product_id'][0], item['product_qty']) for item in
            MrpPlan.read_group(
                [('date_finish', '<', init_date)] + domain_in,
                ['product_id', 'product_qty'],
                ['product_id'])
        )
        moves_out_init = dict(
            (item['product_id'][0], item['product_qty']) for item in
            MrpPlan.read_group(
                [('date_start', '<', init_date)] + domain_out,
                ['product_id', 'product_qty'],
                ['product_id'])
        )

        # get planned moves, after the initial bucket date, grouped by bucket dates
        moves_in = dict(
            ((item['product_id'][0], item[date_group_in]), item['product_qty']) for item in
            MrpPlan.read_group(
                [('date_finish', '>=', init_date)] + domain_in,
                ['product_id', 'date_finish', 'product_qty'],
                ['product_id', date_group_in],
                lazy=False)
        )
        moves_out = dict(
            ((item['product_id'][0], item[date_group_out]), item['product_qty']) for item in
            MrpPlan.read_group(
                [('date_start', '>=', init_date)] + domain_out,
                ['product_id', 'date_start', 'product_qty'],
                ['product_id', date_group_out],
                lazy=False)
        )

        # format bucket dates to match those returned by the read_group() method
        def format_date(dt):
            if bucket_size == 7:
                # odoo date:week doesn't zero pad the week number, but the python %W formatting directive does
                return "W%d %d" % (dt.isocalendar()[1], dt.year)
            else:
                # odoo date:day doesn't returned dates in DEFAULT_SERVER_DATE_FORMAT
                return dt.strftime('%d %b %Y')

        res = dict()
        for product in self.with_context(prefetch_fields=False):
            # if product.id == 13964:
            #     import pdb
            #     pdb.set_trace()
            planned_available = moves_in_init.get(product.id, 0.0)
            planned_available -= moves_out_init.get(product.id, 0.0)
            init_key = (product.id, bucket_list[0])
            res[init_key] = float_round(planned_available, precision_rounding=product.uom_id.rounding)
            for bucket_date in bucket_list[1:]:
                key = (product.id, format_date(bucket_date))
                planned_available += moves_in.get(key, 0.0)
                planned_available -= moves_out.get(key, 0.0)
                res[(product.id, bucket_date)] = float_round(planned_available, precision_rounding=product.uom_id.rounding)

        return res

    @api.multi
    def bucket_virtual_available(self, bucket_list, bucket_size):
        """
        Get virtual available for each product in self, for each bucket date
        :param [datetime] bucket_list: list of bucket dates as datetime objects
        :param int bucket_size: number of days in each bucket
        :return {(int, datetime): float} res: dictionary of quantities as float
        """

        if bucket_list[0] < datetime.now().date():
            raise UserError(_('The beginning bucket date is in the past.  All bucket dates must be in the future.'))
        date_group = bucket_size == 7 and 'date:week' or 'date:day'
        init_date = bucket_list[0].strftime(DEFAULT_SERVER_DATE_FORMAT)

        # for these locations
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations()

        # for these products
        domain_quant = [('product_id', 'in', self.ids)] + domain_quant_loc
        domain_move_in = [('product_id', 'in', self.ids)] + domain_move_in_loc
        domain_move_out = [('product_id', 'in', self.ids)] + domain_move_out_loc

        # pending moves for virtual available
        domain_move_in += [('state', 'not in', ('done', 'cancel', 'draft'))]
        domain_move_out += [('state', 'not in', ('done', 'cancel', 'draft'))]

        # get moves/quants up to the initial bucket date
        Move = self.env['stock.move']
        Quant = self.env['stock.quant']
        moves_in_res_init = dict(
            (item['product_id'][0], item['product_qty']) for item in
            Move.read_group(
                [('date', '<', init_date)] + domain_move_in,
                ['product_id', 'product_qty'],
                ['product_id'])
        )
        moves_out_res_init = dict(
            (item['product_id'][0], item['product_qty']) for item in
            Move.read_group(
                [('date', '<', init_date)] + domain_move_out,
                ['product_id', 'product_qty'],
                ['product_id'])
        )
        quants_res = dict((item['product_id'][0], item['qty']) for item in
                          Quant.read_group(domain_quant, ['product_id', 'qty'], ['product_id']))

        # get moves grouped by bucket dates
        moves_in_res = dict(
            ((item['product_id'][0], item[date_group]), item['product_qty']) for item in
            Move.read_group(
                [('date', '>=', init_date)] + domain_move_out,
                ['product_id', 'date', 'product_qty'],
                ['product_id', date_group],
                lazy=False)
        )
        moves_out_res = dict(
            ((item['product_id'][0], item[date_group]), item['product_qty']) for item in
            Move.read_group(
                [('date', '>=', init_date)] + domain_move_out,
                ['product_id', 'date', 'product_qty'],
                ['product_id', date_group],
                lazy=False)
        )

        # format bucket dates to match those returned by the read_group() method
        def format_date(dt):
            if bucket_size == 7:
                # odoo date:week doesn't zero pad the week number, but the python %W formatting directive does
                return "W%d %d" % (dt.isocalendar()[1], dt.year)
            else:
                # odoo date:day doesn't returned dates in DEFAULT_SERVER_DATE_FORMAT
                return dt.strftime('%d %b %Y')

        res = dict()
        for product in self.with_context(prefetch_fields=False):
            virtual_available = quants_res.get(product.id, 0.0)
            virtual_available += moves_in_res_init.get(product.id, 0.0)
            virtual_available -= moves_out_res_init.get(product.id, 0.0)
            init_key = (product.id, bucket_list[0])
            res[init_key] = float_round(virtual_available, precision_rounding=product.uom_id.rounding)
            for bucket_date in bucket_list[1:]:
                key = (product.id, format_date(bucket_date))
                virtual_available += moves_in_res.get(key, 0.0)
                virtual_available -= moves_out_res.get(key, 0.0)
                res[(product.id, bucket_date)] = float_round(virtual_available, precision_rounding=product.uom_id.rounding)

        return res

    @api.multi
    def get_procurement_action(self, location=None):
        """
        Return true if this product should be manufactured, based on procurement rule
        We may want to add an interface to the procurement.rule model, so users can change the sequence
        :returns procurement.rule.action :
         - move
         - buy
         - manufacture
         - ...
         - unknown
        """
        self.ensure_one()

        domain = []
        if location:
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
        product_routes = self.route_ids | self.categ_id.total_route_ids
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

