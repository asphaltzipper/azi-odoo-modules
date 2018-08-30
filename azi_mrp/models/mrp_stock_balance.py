# -*- coding: utf-8 -*-


from odoo import api, fields, models, tools
from odoo.addons import decimal_precision as dp


class MrpStockBalance(models.Model):
    _name = 'mrp.stock.balance'
    _auto = False
    _order = 'over_value desc'

    # these fields selected from the database view
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        index=True,
        required=True)
    categ_id = fields.Many2one(
        comodel_name='product.category',
        string='Category')
    e_kanban = fields.Boolean(
        string='E-Kanban',
        default=False,
        help="Material planning (MRP) for This product will be handled by electronic kanban")
    product_type = fields.Selection(
        # selection=dict(self.env['product.template'].fields_get(allfields=['type'])['type']['selection'])['key'],
        selection=[
            ('product', 'Stockable'),
            ('consu', 'Consumable'),
            ('service', 'Service')],
        string='Product Type',
        required=True)
    uom_id = fields.Many2one(
        comodel_name='product.uom',
        string='UOM')
    supply_names = fields.Char(
        string='Supply',
        help="Supply method names")
    wc_codes = fields.Char(
        string='Route',
        help="Production routing workcenter")
    min_qty = fields.Float(
        string='Min',
        digits=(16, 0))
    onhand_qty = fields.Float(
        string='Onhand',
        digits=(16, 0))
    move_in_qty = fields.Float(
        string='Move In',
        digits=(16, 0))
    move_out_qty = fields.Float(
        string='Move Out',
        digits=(16, 0))
    planned_qty = fields.Float(
        string='Planned',
        digits=(16, 0))
    delivered_qty = fields.Float(
        string='Sold',
        digits=(16, 0))
    ending_qty = fields.Float(
        string='Ending',
        digits=(16, 0))
    over_qty = fields.Float(
        string='Excess',
        digits=(16, 0))
    over_value = fields.Float(
        string='Excess Value',
        digits=(16, 0))

    def action_material_analysis(self):
        self.ensure_one()
        return self.product_id.action_material_analysis()

    def action_material_analysis_pop(self):
        self.ensure_one()
        return self.with_context(pop_graph=True).product_id.action_material_analysis()

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'mrp_stock_balance')
        self._cr.execute("""
            CREATE VIEW mrp_stock_balance AS (
                select
                    pp.id,
                    pp.id as product_id,
                    pt.categ_id,
                    pp.e_kanban,
                    pt.type as product_type,
                    pt.uom_id,
                    s.supply_names,
                    r.wc_codes,
                    coalesce(op.product_min_qty) as min_qty,
                    oh.onhand_qty,
                    coalesce(im.move_in_qty,0.0) as move_in_qty,
                    coalesce(om.move_out_qty,0.0) as move_out_qty,
                    coalesce(pl.planned_qty, 0.0) as planned_qty,
                    coalesce(dl.delivered_qty, 0.0) as delivered_qty,
                    coalesce(oh.onhand_qty,0.0) + coalesce(im.move_in_qty,0.0) + coalesce(om.move_out_qty,0.0) + coalesce(pl.planned_qty,0.0) as ending_qty,
                    coalesce(oh.onhand_qty,0.0) + coalesce(im.move_in_qty,0.0) + coalesce(om.move_out_qty,0.0) + coalesce(pl.planned_qty,0.0) - coalesce(op.product_min_qty, 0.0) as over_qty,
                    (coalesce(oh.onhand_qty,0.0) + coalesce(im.move_in_qty,0.0) + coalesce(om.move_out_qty,0.0) + coalesce(pl.planned_qty,0.0) - coalesce(op.product_min_qty, 0.0)) * coalesce(pc.value_float, 0.0) as over_value
                from product_product as pp
                left join product_template as pt on pt.id=pp.product_tmpl_id
                left join ir_property as pc on pc.name='standard_price' and pc.res_id='product.product,'||pp.id
                left join product_category as c on c.id=pt.categ_id
                left join stock_warehouse_orderpoint as op on op.product_id=pp.id
                left join (
                    -- current on-hand quantity
                    select
                        m.product_id,
                        sum(case when src.usage='internal' then m.product_uom_qty*-1 else m.product_uom_qty end) as onhand_qty
                    from stock_move as m
                    left join stock_location as src on src.id=m.location_id
                    left join stock_location as dst on dst.id=m.location_dest_id
                    where m.state='done'
                    and (
                        (src.usage='internal' and dst.usage<>'internal')
                        or
                        (src.usage<>'internal' and dst.usage='internal')
                    )
                    group by m.product_id
                ) as oh on oh.product_id=pp.id
                left join (
                    -- impending moves inbound
                    select
                        m.product_id,
                        sum(m.product_uom_qty) as move_in_qty
                    from stock_move as m
                    left join stock_location as src on src.id=m.location_id
                    left join stock_location as dst on dst.id=m.location_dest_id
                    where m.state not in ('done', 'cancel')
                    and src.usage<>'internal'
                    and dst.usage='internal'
                    group by m.product_id
                ) as im on im.product_id=pp.id
                left join (
                    -- impending moves outbound
                    select
                        m.product_id,
                        sum(m.product_uom_qty*-1) as move_out_qty
                    from stock_move as m
                    left join stock_location as src on src.id=m.location_id
                    left join stock_location as dst on dst.id=m.location_dest_id
                    where m.state not in ('done', 'cancel')
                    and src.usage='internal'
                    and dst.usage<>'internal'
                    group by m.product_id
                ) as om on om.product_id=pp.id
                left join (
                    -- planned moves quantity
                    select
                        product_id,
                        sum(case when move_type='supply' then product_qty else product_qty*-1 end) as planned_qty
                    from mrp_material_plan
                    group by product_id
                ) as pl on pl.product_id=pp.id
                left join (
                    -- supply methods
                    select
                        product_id as product_tmpl_id,
                        string_agg(name, ', ') as supply_names
                    from stock_route_product as sr
                    left join stock_location_route as r on r.id=sr.route_id
                    group by product_id
                ) as s on s.product_tmpl_id=pt.id
                left join (
                    -- routing workcenters
                    select
                        product_id,
                        string_agg(code::varchar, ',') as wc_codes
                    from (
                        select distinct
                            b.product_id,
                            r.code
                        from mrp_routing_workcenter as rw
                        left join mrp_workcenter as w on w.id=rw.workcenter_id
                        left join resource_resource as r on r.id=w.resource_id
                        left join (
                            select distinct on (product_id) *
                            from mrp_bom
                            where active=true
                            order by product_id, version desc, sequence
                        ) as b on b.routing_id=rw.routing_id
                        order by b.product_id, r.code
                    ) as t
                    group by product_id
                ) as r on r.product_id=pp.id
                left join (
                    -- deliveries in the last 2 years
                    select
                        product_id,
                        sum(product_uom_qty) as delivered_qty
                    from stock_move as m
                    left join stock_location as src on src.id=m.location_id
                    where src.usage='internal'
                    and location_dest_id=9 -- stock.stock_location_customers
                    and date > now() - interval '2 year'
                    and state='done'
                    group by product_id
                ) as dl on dl.product_id=pp.id
                where c.eng_management=true
            )
        """)
