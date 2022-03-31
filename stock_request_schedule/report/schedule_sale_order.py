# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools


class ScheduleSaleOrder(models.AbstractModel):
    _name = 'report.stock_request_schedule.report_schedule_so'
    _description = 'Compare SO with SR'

    @api.model
    def get_html(self):
        res = self._get_report_data()
        res['lines'] = self.env.ref('stock_request_schedule.report_schedule_so').render({'data': res})
        return res

    @api.model
    def _get_report_data(self):
        unschedule_so_without_reserved = self.get_unschedule_so_without_reserved()
        schedule_so_with_reserved = self.get_schedule_so_with_reserved()
        schedule_so_with_diff_date = self.get_schedule_so_with_diff_date()
        return {
            'unschedule_without_reserved': unschedule_so_without_reserved,
            'schedule_so_with_reserved': schedule_so_with_reserved,
            'schedule_so_with_diff_date': schedule_so_with_diff_date,
        }

    def get_unschedule_so_without_reserved(self):
        self._cr.execute("""
            select
                so.name, pp.default_code, pt.name, so.id, spl.name
            from sale_order_line sol
            left join sale_order so on so.id=sol.order_id
            left join product_product pp on pp.id=sol.product_id
            left join product_template pt on pt.id=pp.product_tmpl_id left join product_category pc on pc.id=pt.categ_id
            left join (
                select *
                from stock_request
                where state in ('submitted', 'draft', 'open')
                ) sr on sr.sale_order_line_id=sol.id 
            left join (
                select *
                from stock_move
                where state not in ('cancel')
                ) sm on sm.sale_line_id=sol.id
            left join stock_move_line sml on sml.move_id=sm.id left join stock_production_lot spl on spl.id=sml.lot_id where sol.delivery_remaining_qty>0
            and so.state='sale'
            and pc.name ilike 'FG - %'
            and sml.lot_id is null
            and sr.id is null
        """)
        return self._cr.fetchall()

    def get_schedule_so_with_reserved(self):
        self._cr.execute("""
            select
                so.name,
                pp.default_code, pt.name,
                so.id,
                spl.name
            from sale_order_line sol
            left join sale_order so on so.id=sol.order_id
            left join product_product pp on pp.id=sol.product_id
            left join product_template pt on pt.id=pp.product_tmpl_id left join product_category pc on pc.id=pt.categ_id
            left join (
                select *
                from stock_request
                where state in ('submitted', 'draft', 'open')
                ) sr on sr.sale_order_line_id=sol.id 
            left join (
                select *
                from stock_move
                where state not in ('cancel')
                ) sm on sm.sale_line_id=sol.id
            left join stock_move_line sml on sml.move_id=sm.id left join stock_production_lot spl on spl.id=sml.lot_id where sol.delivery_remaining_qty>0
            and so.state='sale'
            and pc.name ilike 'FG - %'
            and sml.lot_id is not null
            and sr.id is not null
        """)
        return self._cr.fetchall()

    def get_schedule_so_with_diff_date(self):
        self._cr.execute("""
            select
                so.name,
                pp.default_code,
                pt.name,
                sm.date::date as so_date,
                sr.expected_date::date as sr_date,
                round((extract(epoch from sm.date) / 86400 - extract(epoch
            from sr.expected_date) / 86400)::decimal, 0) as day_diff
            from sale_order_line sol 
            left join sale_order so on so.id = sol.order_id
            left join product_product pp on pp.id = sol.product_id
            left join product_template pt on pt.id = pp.product_tmpl_id
            left join product_category pc on pc.id = pt.categ_id
            left join(
                select *
                from stock_request
                where
                state in ('submitted', 'draft', 'open')
            ) sr on sr.sale_order_line_id = sol.id
            left join(
                select *
                from stock_move
                where
                state not in ('cancel')
            ) sm on  sm.sale_line_id = sol.id
            left join stock_move_line sml on sml.move_id = sm.id
            left join stock_production_lot spl on spl.id = sml.lot_id
            where sol.delivery_remaining_qty > 0
            and so.state = 'sale'
            and pc.name ilike 'FG - %'
            and sr.id is not null
            and abs(round((extract(epoch from sm.date) / 86400 - extract(epoch from sr.expected_date) / 86400)::decimal, 0)) >1
        """)
        return self._cr.fetchall()
