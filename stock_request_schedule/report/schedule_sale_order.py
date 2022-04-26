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
        schedule_so_with_diff_product = self.get_schedule_so_with_diff_product()
        schedule_so_with_early_date = self.get_schedule_so_with_early_date()
        schedule_so_with_late_date = self.get_schedule_so_with_late_date()
        return {
            'unschedule_without_reserved': unschedule_so_without_reserved,
            'schedule_so_with_reserved': schedule_so_with_reserved,
            'schedule_so_with_diff_product': schedule_so_with_diff_product,
            'schedule_so_with_early_date': schedule_so_with_early_date,
            'schedule_so_with_late_date': schedule_so_with_late_date,
        }

    def get_unschedule_so_without_reserved(self):
        self._cr.execute("""
            select
                so.name,
                pp.default_code,
                pt.name,
                spl.name,
                so.id
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
                spl.name,
                so.id
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

    def get_schedule_so_with_diff_product(self):
        self._cr.execute("""
            select
                so.id as so_id,
                so.name as so_name,
                ppo.default_code as so_prod_code,
                pto.name as so_prod_name,
                sr.id as sr_id,
                sr.name as sr_name,
                ppr.default_code as sr_prod_code,
                ptr.name as sr_prod_name
            from sale_order_line sol
            left join sale_order so on so.id=sol.order_id
            left join product_product ppo on ppo.id=sol.product_id
            left join product_template pto on pto.id=ppo.product_tmpl_id
            left join product_category pco on pco.id=pto.categ_id
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
            left join stock_move_line sml on sml.move_id=sm.id
            left join product_product ppr on ppr.id=sr.product_id
            left join product_template ptr on ptr.id=ppr.product_tmpl_id
            where sol.delivery_remaining_qty>0
            and so.state='sale'
            and pco.name ilike 'FG - %'
            and sr.id is not null
            and sol.product_id<>sr.product_id
        """)
        return self._cr.fetchall()

    def get_schedule_so_with_early_date(self):
        self._cr.execute("""
            select
                so.id,
                so.name,
                pp.default_code,
                pt.name,
                sm.date_expected::date as so_date,
                sr.id,
                sr.name,
                sr.expected_date::date as sr_date,
                round((extract(epoch from sm.date_expected::date) / 86400 - extract(epoch from sr.expected_date::date) / 86400)::decimal, 0) as day_diff
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
            and round((extract(epoch from sm.date_expected::date) / 86400 - extract(epoch from sr.expected_date::date) / 86400)::decimal, 0)<0
        """)
        return self._cr.fetchall()

    def get_schedule_so_with_late_date(self):
        self._cr.execute("""
            select
                so.id,
                so.name,
                pp.default_code,
                pt.name,
                sm.date_expected::date as so_date,
                sr.id,
                sr.name,
                sr.expected_date::date as sr_date,
                round((extract(epoch from sm.date_expected::date) / 86400 - extract(epoch from sr.expected_date::date) / 86400)::decimal, 0) as day_diff
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
            and round((extract(epoch from sm.date_expected::date) / 86400 - extract(epoch from sr.expected_date::date) / 86400)::decimal, 0)>0
        """)
        return self._cr.fetchall()
