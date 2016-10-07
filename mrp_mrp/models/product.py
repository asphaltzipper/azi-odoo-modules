# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, float_round
from odoo.exceptions import UserError


class Product(models.Model):
    _inherit = "product.product"

    @api.multi
    def planned_virtual_available(self, to_date=None):
        """Return planned net move quantity, for select products, through the given date"""

        # build domain for searching mrp.material_plan records
        domain = [('product_id', 'in', self.ids)]
        if to_date:
            domain += [('date_finish', '<', datetime.strftime(to_date, DEFAULT_SERVER_DATE_FORMAT))]
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
            qty = moves_in.get(product.id, 0.0) - moves_out.get(product.id, 0.0)
            res[product.id] = float_round(qty, precision_rounding=product.uom_id.rounding)
        return res

    @api.multi
    def bucket_planned_available(self, bucket_list, bucket_size):
        """Return planned net move quantity, for select products, grouped by bucket date"""

        # if 2064 in self.ids:
        #     import pdb
        #     pdb.set_trace()

        if bucket_list[0] < datetime.now().date():
            raise UserError(_('The beginning bucket date is in the past.  All bucket dates must be in the future.'))
        date_group_out = bucket_size == 7 and 'date_start:week' or 'date_start:day'
        date_group_in = bucket_size == 7 and 'date_finish:week' or 'date_finish:day'
        # TODO: why is date:day not returned in DEFAULT_SERVER_DATE_FORMAT?
        date_format = bucket_size == 7 and 'W%W %Y' or '%d %b %Y'
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
                [('date_finish', '<', init_date)] + domain_out,
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
                [('date_finish', '>=', init_date)] + domain_out,
                ['product_id', 'date_start', 'product_qty'],
                ['product_id', date_group_out],
                lazy=False)
        )

        res = dict()
        for product in self.with_context(prefetch_fields=False):
            planned_available = moves_in_init.get(product.id, 0.0)
            planned_available -= moves_out_init.get(product.id, 0.0)
            init_key = (product.id, bucket_list[0])
            res[init_key] = float_round(planned_available, precision_rounding=product.uom_id.rounding)
            for bucket_date in bucket_list[1:]:
                key = (product.id, bucket_date.strftime(date_format))
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
        # TODO: why is date:day not returned in DEFAULT_SERVER_DATE_FORMAT?
        date_format = bucket_size == 7 and 'W%W %Y' or '%d %b %Y'
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

        res = dict()
        for product in self.with_context(prefetch_fields=False):
            virtual_available = quants_res.get(product.id, 0.0)
            virtual_available += moves_in_res_init.get(product.id, 0.0)
            virtual_available -= moves_out_res_init.get(product.id, 0.0)
            init_key = (product.id, bucket_list[0])
            res[init_key] = float_round(virtual_available, precision_rounding=product.uom_id.rounding)
            for bucket_date in bucket_list[1:]:
                key = (product.id, bucket_date.strftime(date_format))
                virtual_available += moves_in_res.get(key, 0.0)
                virtual_available -= moves_out_res.get(key, 0.0)
                res[(product.id, bucket_date)] = float_round(virtual_available, precision_rounding=product.uom_id.rounding)

        return res
