from odoo import models, api, fields, tools, _


class SOLineReport(models.Model):
    _name = 'so.line.report'
    _description = 'SO Lines Report'
    _auto = False

    order_name = fields.Char('SO Name')
    order_line_name = fields.Char('Line Name')
    confirm_date = fields.Date('Date')
    customer_name = fields.Char('Customer')
    state = fields.Char('State')
    wc_code = fields.Char('Code')
    route_name = fields.Char('Route Names')
    salesperson = fields.Char('Salesperson')

    def init(self):
        tools.drop_view_if_exists(self._cr, 'so_line_report')
        self._cr.execute("""
            CREATE VIEW so_line_report AS (
                with route_detail as (
                    select
                        product_id,
                        string_agg("sequence"::varchar, ',') as seq_nums,
                        string_agg(code::varchar, ',') as wc_code
                    from (
                        select distinct
                            b.product_id,
                            rw."sequence",
                            w.code
                        from mrp_routing_workcenter as rw
                        left join mrp_workcenter as w on w.id=rw.workcenter_id
                        left join (
                            select distinct on (product_id) *
                            from mrp_bom
                            where active=true
                            order by product_id, version desc, "sequence"
                        ) as b on b.id=rw.bom_id
                        order by b.product_id, rw."sequence", w.code
                    ) as t
                    group by product_id
                )
                select
                    sol.id as id,
                    so.name as order_name,
                    --pp.default_code as pn,
                    --pt.name as name,
                    sol.name as order_line_name,
                    coalesce(so.commitment_date, so.effective_date, so.date_order)::date as "confirm_date",
                    rp.name as customer_name,
                    rcs.name as state,
                    rd.wc_code,
                    sr.route_name,
                    rp2.name as salesperson
                from sale_order_line sol
                left join sale_order so on so.id=sol.order_id
                left join product_product pp on pp.id=sol.product_id
                left join product_template pt on pt.id=pp.product_tmpl_id
                left join product_category pc on pc.id=pt.categ_id
                left join res_partner rp on rp.id=so.partner_id
                left join res_country_state rcs on rcs.id=rp.state_id
                left join route_detail rd on rd.product_id=pp.id
                left join res_users ru on ru.id=so.user_id
                left join res_partner rp2 on rp2.id=ru.partner_id
                left join (
                    select
                        srp.product_id,
                        string_agg(slr.name ->> 'en_US', ' ') as route_name,
                        string_agg(srp.route_id::varchar, ' ') as route_ids
                    from stock_route_product srp
                    left join stock_route slr on slr.id=srp.route_id
                    group by srp.product_id
                ) as sr on sr.product_id=pp.id
                where so.state='sale'
                and sol.qty_delivered < sol.product_uom_qty
                and pc.name<>'Shipping & Handling'
                and pt.name ->> 'en_US' not in (
                    'Customer Sale Deposit',
                    'Restocking Fee',
                    'Rental Repair Services',
                    'Machine Rental',
                    'MSO Services'
                )
                and rp2.name<>'Doug Angus'
                order by coalesce(so.commitment_date, so.effective_date)
            )
        """)
