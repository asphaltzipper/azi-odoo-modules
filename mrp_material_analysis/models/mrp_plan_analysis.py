# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
from odoo.addons import decimal_precision as dp


class MrpPlanAnalysis(models.Model):
    _name = 'mrp.plan.analysis'
    _auto = False

    # these fields selected from the database view
    plan_line_id = fields.Many2one(
        comodel_name='mrp.material_plan',
        string='Plan Line',
        required=True)

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True)

    categ_id = fields.Many2one(
        comodel_name='product.category',
        string='Category',
        required=True)

    product_type = fields.Selection(
        # selection=dict(self.env['product.template'].fields_get(allfields=['type'])['type']['selection'])['key'],
        selection=[
            ('product', 'Stockable'),
            ('consu', 'Consumable'),
            ('service', 'Service')],
        string='Product Type',
        required=True)

    deprecated = fields.Boolean(
        string='Obsolete',
        required=True)

    e_kanban = fields.Boolean(
        string='BinItem',
        required=True)

    product_qty = fields.Float(
        string='Quantity',
        digits=dp.get_precision('Product Unit of Measure'),
        required=True)

    uom_id = fields.Many2one(
        comodel_name='product.uom',
        string="UOM",
        related='product_id.uom_id')

    make = fields.Boolean(
        string='Manufactured',
        required=True)

    date_start = fields.Date(
        string='Start Date',
        required=True)

    date_finish = fields.Date(
        string='Finish Date',
        required=True)

    lead_days = fields.Integer(
        string='LeadDays',
        required=True)

    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location',
        required=True)

    origin = fields.Char(
        string='Origin',
        required=True)

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Supplier')

    date_exp_order = fields.Date(
        string='Expedite Order Date')

    expedite_days = fields.Integer(
        string='ExpediteDays',
        help="Number of days earlier the order would have to be received")

    expedite_window = fields.Integer(
        string="ExpediteWindow",
        help="A percentage of the lead-time days remaining before the order is due to be delivered")

    expedite_qty = fields.Float(
        string="ExpediteQty")

    exp_group_id = fields.Many2one(
        comodel_name='procurement.group',
        string="ExpediteGroup")

    date_incr_order = fields.Date(
        string='Increase Order Date',
        required=True)

    trailing_days = fields.Integer(
        string='ExpediteDays',
        help="Number of days earlier the order would have to be received")

    increase_qty = fields.Float(
        string="IncreaseQty",
        help="The original quantity on the order to be increased")

    incr_group_id = fields.Many2one(
        comodel_name='procurement.group',
        string="IncreaseGroup")

    increase_window = fields.Integer(
        string="IncreaseWindow",
        help="A percentage of the lead-time days remaining before the order is due to be delivered")

    blanket_id = fields.Many2one(
        comodel_name='purchase.requisition',
        string='Blanket Order')

    def action_material_analysis(self):
        self.ensure_one()
        return self.product_id.action_material_analysis()

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'mrp_plan_analysis')
        self._cr.execute("""
            CREATE VIEW mrp_plan_analysis AS (
                select
                    mp.id,
                    mp.id as plan_line_id,
                    mp.product_id,
                    t.categ_id,
                    t.type as product_type,
                    p.deprecated,
                    mp.e_kanban,
                    p.default_code,
                    t.name as product_name,
                    mp.product_qty,
                    t.uom_id,
                    mp.make,
                    mp.date_start,
                    mp.date_finish,
                    (mp.date_finish - mp.date_start) as lead_days,
                    mp.location_id,
                    mp.origin,
                    ds.name as partner_id,
                    x.date_expected as date_exp_order,
                    x.expedite_days,
                    round(x.expedite_window * 100) as expedite_window,
                    x.real_qty as expedite_qty,
                    x.group_id as exp_group_id,
                    i.date_expected as date_incr_order,
                    i.trailing_days,
                    i.real_qty as increase_qty,
                    i.group_id as incr_group_id,
                    i.increase_window,
                    b.blanket_id
                from mrp_material_plan as mp
                left join product_product as p on p.id=mp.product_id
                left join product_template as t on t.id=p.product_tmpl_id
                left join (
                    select distinct on (product_tmpl_id) *
                    from product_supplierinfo
                    order by product_tmpl_id, sequence desc
                ) as ds on ds.product_tmpl_id=t.id
                left join (
                    -- open blanket orders
                    select distinct on (product_id)
                        l.product_id,
                        r.id as blanket_id
                    from purchase_requisition_line as l
                    left join purchase_requisition as r on r.id=l.requisition_id
                    where r.type_id=1
                    and r.state not in ('done', 'cancel')
                    order by product_id, ordering_date
                ) as b on b.product_id=mp.product_id
                left join (
                    -- expedite
                    -- real supply within lead time, looking forward
                    select distinct on (p.id)
                        p.id,
                        m.date_expected::date as date_expected,
                        m.date_expected::date - p.date_finish as expedite_days,
                        (m.date_expected::date - now()::date)::numeric / (p.date_finish - p.date_start)::numeric as expedite_window,
                        m.product_uom_qty as real_qty,
                        m.group_id
                    from mrp_material_plan as p
                    inner join stock_move as m on m.product_id=p.product_id and m.location_dest_id=p.location_id
                    where p.move_type='supply'
                    and m.state not in ('done', 'cancel')
                    and m.date_expected>p.date_finish
                    and m.date_expected<(p.date_finish + (p.date_finish - p.date_start))
                    order by p.id, expedite_days
                ) as x on x.id=mp.id
                left join (
                    -- increase
                    -- real supply within lead time, looking backward
                    select distinct on (p.id)
                        p.id,
                        m.date_expected::date as date_expected,
                        p.date_finish - m.date_expected::date as trailing_days,
                        (m.date_expected::date - now()::date)::numeric / (p.date_finish - p.date_start)::numeric as increase_window,
                        m.product_uom_qty as real_qty,
                        m.group_id
                    from mrp_material_plan as p
                    inner join stock_move as m on m.product_id=p.product_id and m.location_dest_id=p.location_id
                    where p.move_type='supply'
                    and m.state not in ('done', 'cancel')
                    and m.date_expected>p.date_start
                    and m.date_expected<p.date_finish
                    order by p.id, trailing_days
                ) as i on i.id=mp.id
                where mp.move_type='supply'
                order by mp.date_start
            )
        """)
