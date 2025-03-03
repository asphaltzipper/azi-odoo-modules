# Copyright 2025 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, _
from odoo.exceptions import UserError


class OperationsRecursionLine(models.TransientModel):
    _name = 'operations.recursion.line'
    _description = 'MRP Operations Recursion Line'
    _order = 'code_path'

    top_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Top Product',
        required=True,
        ondelete="cascade",
        index=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        ondelete="cascade",
        index=True,
    )
    workcenter_id = fields.Many2one(
        comodel_name="mrp.workcenter",
        string="Operation",
        ondelete="cascade",
        index=True,
    )
    code_path = fields.Char(
        string="BOM Path",
        index=True,
    )
    bom_id = fields.Many2one(
        comodel_name='mrp.bom',
        string='BOM',
        ondelete="cascade",
    )
    multiplied_qty = fields.Float(
        string="Tx Qty",
        digits='Product Unit of Measure',
    )
    time_cycle = fields.Float(
        string="Time",
    )

    def get_operations_recursion(self, bom):
        bom.ensure_one()
        if not bom.product_id:
            raise UserError(_("BOM must include Product Variant"))

        dom = [
            ('top_product_id', '=', bom.product_id.id),
            ('create_uid', '=', self._uid),
        ]
        self.search(dom).unlink()

        sql = """
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
bom_path(top_parent_id, comp_id, parent_id, code_path, mult_qty) as (
        select
            pp.id as top_parent_id,
            pp.id as comp_id,
            0 as parent_id,
            coalesce(pp.default_code, pt.name->>'en_US') as code_path,
            1.0 as mult_qty
        from default_bom as db
        left join product_product pp on pp.id=db.product_id
        left join product_template pt on pt.id=db.product_tmpl_id
        where db.id=%(bom_id)s
    union
        select
            p.top_parent_id,
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
    b.top_parent_id,
    b.comp_id as product_id,
    mrw.workcenter_id,
    b.code_path,
    db.id as bom_id,
    b.mult_qty as multiplied_qty,
    (coalesce(wd.avg_duration_unit, 0) * b.mult_qty) / 60 as time_cycle
from bom_path as b
left join clean_bom as cb on cb.parent_prod_id=b.parent_id and cb.comp_prod_id=b.comp_id
left join default_bom as db on db.product_id=b.comp_id
left join product_product as pp on pp.id=b.top_parent_id
left join product_product as cp on cp.id=b.comp_id
left join mrp_routing_workcenter mrw on mrw.bom_id=db.id
left join work_duration wd on wd.product_id=b.comp_id and wd.workcenter_id=mrw.workcenter_id
left join supply_methods as sm on sm.product_tmpl_id=cp.product_tmpl_id
where sm.supply_names='Manufacture'
and coalesce(db."type", '')<>'phantom'
order by b.code_path
        """
        self.env.cr.execute(sql, {'avg_len': 10, 'bom_id': bom.id})

        vals_list = [{
            'top_product_id': x[0],
            'product_id': x[1],
            'workcenter_id': x[2],
            'code_path': x[3],
            'bom_id': x[4],
            'multiplied_qty': x[5],
            'time_cycle': x[6],
        } for x in self.env.cr.fetchall()]

        self.create(vals_list)

        action = self.env["ir.actions.actions"]._for_xml_id(
            'stock_forecast_detail.action_operations_recursion_line_tree')
        action['domain'] = [
            ('top_product_id', '=', bom.product_id.id),
            ('create_uid', '=', self._uid),
        ]
        return action

