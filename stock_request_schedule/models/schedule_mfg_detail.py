from odoo import api, fields, models, tools


class ScheduleMfgDetail(models.Model):
    _name = "schedule.mfg.detail"
    _description = "Stock Request Schedule Manufacturing Operation Detail"
    _auto = False

    # fields selected from the database view
    stock_request_id = fields.Many2one(
        comodel_name="stock.request",
        string="SR",
    )
    expected_date = fields.Datetime(
        string="Schedule Date",
    )
    top_prod_id = fields.Many2one(
        comodel_name="product.product",
        string = "Scheduled Variant"
    )
    top_tmpl_id = fields.Many2one(
        comodel_name="product.template",
        string="Scheduled Product",
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Variant",
    )
    product_tmpl_id = fields.Many2one(
        comodel_name="product.template",
        string="Product",
    )
    bom_id = fields.Many2one(
        comodel_name="mrp.bom",
        string="BOM",
    )
    workcenter_id = fields.Many2one(
        comodel_name="mrp.workcenter",
        string="Operation",
    )
    multiplied_qty = fields.Float(
        string="Qty",
    )
    status = fields.Char(
        string="Status",
    )
    code_path = fields.Char(
        string="BOM Path",
    )
    time_cycle = fields.Float(
        string="Time",
    )

    # related fields
    # time_cycle = fields.Float(
    #     string='Duration',
    #     compute="_compute_time_cycle",
    # )
    config_code = fields.Char(
        related='top_prod_id.config_code',
        string="Config",
    )

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'schedule_mfg_detail')
        sql = """
CREATE VIEW schedule_mfg_detail AS (
    with recursive default_bom as (
        select distinct on (product_id) *
        from mrp_bom
        where active=true
        and product_id is not null
        order by product_id, "version" desc, "sequence"
    ),
    clean_bom (parent_tmpl_id, parent_prod_id, line_id, comp_prod_id, "type", product_qty) as (
        select
            b.product_tmpl_id as parent_tmpl_id,
            b.product_id as parent_prod_id,
            l.id as line_id,
            l.product_id as comp_prod_id,
            b."type",
            l.product_qty
        from mrp_bom_line as l
        inner join default_bom as b on b.id=l.bom_id
    ),
    supply_methods as (
        select
            product_id as product_tmpl_id,
            string_agg(name->>'en_US', ', ') as supply_names
        from stock_route_product as sr
        left join stock_route as r on r.id=sr.route_id
        group by product_id
    ),
    work_duration as (
        -- manufacturing order work duration per unit averaged over latest 5
        select
            t.product_id,
            t.workcenter_id,
            avg(duration_unit) as avg_duration_unit
        from (
            select
                mp.product_id,
                mw.workcenter_id,
                mp.date_finished,
                sum(mw.duration_unit) duration_unit,
                rank() over (partition by mp.product_id order by mp.date_finished desc) as date_rank
            from mrp_workorder mw
            left join mrp_production mp on mp.id=mw.production_id
            where mp.state='done'
            and mw.state='done'
            and mw.duration_unit<>0
            group by mp.product_id, mp.date_finished, mw.workcenter_id
        ) as t
        where t.date_rank<=%(avg_len)s
        group by t.product_id, t.workcenter_id
    ),
    state_names as (
        select
            imfs.value as sel_value,
            imfs.name->>'en_US' as sel_name
        from ir_model_fields_selection imfs
        left join ir_model_fields imf on imf.id=imfs.field_id
        where imf.model='stock.request'
        and imf.name='state'
    ),
    bom_path(stock_request_id, comp_id, parent_id, code_path, mult_qty) as (
            select
                sr.id as stock_request_id,
                sr.product_id as comp_id,
                0 as parent_id,
                sr.name || ' | ' || coalesce(pp.default_code, pt.name->>'en_US') as code_path,
                sr.product_qty as mult_qty
            from stock_request sr
            left join product_product pp on pp.id=sr.product_id
            left join product_template pt on pt.id=pp.product_tmpl_id
            where sr.scheduled=true
            and sr.state in ('submitted', 'draft', 'open')
            and sr.product_id is not null
        union
            select
                p.stock_request_id,
                b.comp_prod_id,
                b.parent_prod_id,
                p.code_path || ' | ' || coalesce(i.default_code, t.name->>'en_US'),
                p.mult_qty * b.product_qty
            from clean_bom as b
            inner join bom_path as p on b.parent_prod_id=p.comp_id
            left join product_product as i on i.id=b.comp_prod_id
            left join product_template as t on t.id=i.product_tmpl_id
            left join product_product as pp on pp.id=b.parent_prod_id
            left join product_template as pt on pt.id=pp.product_tmpl_id
            left join supply_methods as sm on sm.product_tmpl_id=pp.product_tmpl_id
            where sm.supply_names='Manufacture' -- parent is manufactured
    )
    select
        row_number() over (order by b.code_path, mrw.sequence) as id,
        b.stock_request_id,
        sr.expected_date,
        sr.product_id as top_prod_id,
        sr.product_tmpl_id as top_tmpl_id,
        b.comp_id as product_id,
        pp.product_tmpl_id,
        db.id as bom_id,
        mrw.workcenter_id,
        b.mult_qty as multiplied_qty,
        sn.sel_name as status,
        b.code_path,
        coalesce(wd.avg_duration_unit, 0) * b.mult_qty / 60 as time_cycle
    from bom_path as b
    left join clean_bom as cb on cb.parent_prod_id=b.parent_id and cb.comp_prod_id=b.comp_id
    left join default_bom as db on db.product_id=b.comp_id
    left join product_product as pp on pp.id=b.comp_id
    left join mrp_routing_workcenter mrw on mrw.bom_id=db.id
    left join work_duration wd on wd.product_id=b.comp_id and wd.workcenter_id=mrw.workcenter_id
    left join stock_request sr on sr.id=b.stock_request_id
    left join supply_methods as sm on sm.product_tmpl_id=pp.product_tmpl_id
    left join state_names as sn on sn.sel_value=sr.state
    where sm.supply_names='Manufacture'
    and coalesce(db."type", '')<>'phantom'
    order by b.code_path, mrw.sequence
)
        """
        self.env.cr.execute(sql, {'avg_len': 10})
