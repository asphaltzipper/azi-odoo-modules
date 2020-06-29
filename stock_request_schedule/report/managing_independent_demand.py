# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class ManagingIndependentDemand(models.Model):
    _name = 'managing.independent.demand'
    _auto = False

    stock_request_id = fields.Many2one('stock.request', 'Stock Request', required=1)
    product_id = fields.Many2one('product.product', 'Product')
    finished_goods = fields.Boolean('Finished Goods')
    expected_date = fields.Datetime('Expected Date')
    sale_order_line_id = fields.Many2one('sale.order.line', 'Sale Order Line')
    move_ids = fields.Many2many('stock.move', string='Stock Moves', compute='_compute_move_ids')

    @api.depends('sale_order_line_id')
    def _compute_move_ids(self):
        for record in self:
            if record.sale_order_line_id:
                record.move_ids = record.sale_order_line_id.move_ids

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'managing_independent_demand')
        self._cr.execute("""
            CREATE VIEW managing_independent_demand AS (
                select 
                    concat(extract (year from r.expected_date), '/', extract (week from r.expected_date)) as week_name,
                    r.id as id,
                    r.id as stock_request_id, 
                    r.product_id as product_id,
                    r.finished_goods as finished_goods,
                    r.expected_date as expected_date, 
                    s.id as sale_order_line_id
                from stock_request as r 
                inner join sale_order_line as s on  r.sale_order_line_id = s.id
                where r.finished_goods = True
                group by week_name, r.id, r.product_id, r.expected_date, s.id
            )
        """)

