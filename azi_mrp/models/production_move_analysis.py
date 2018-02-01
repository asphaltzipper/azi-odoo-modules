# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
from odoo.addons import decimal_precision as dp


class ProductionMoveAnalysis(models.Model):
    _name = 'production.move.analysis'
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
        tools.drop_view_if_exists(self._cr, 'production_move_analysis')
        self._cr.execute("""
            CREATE VIEW production_move_analysis AS (
                select
                    m.raw_material_production_id,
                    m.production_id,
                    m.date,
                    m.picking_id,
                    m.sequence,
                    m.origin,
                    m.product_id,
                    m.product_uom_qty,
                    m.product_uom,
                    m.location_id,
                    m.location_dest_id,
                    m.create_date,
                    m.state,
                    t.tracking,
                    t.type as product_type,
                    r.route_names,
                    i.qty as input_qty,
                    s.qty as stock_qty,
                    res.res_qty,
                    res.res_names
                from stock_move as m
                left join product_product as p on p.id=m.product_id
                left join product_template as t on t.id=p.product_tmpl_id
                left join (
                    select
                        product_id,
                        string_agg(name, ', ') as route_names
                    from stock_route_product as sr
                    left join stock_location_route as r on r.id=sr.route_id
                    group by product_id
                ) as r on r.product_id=m.product_id
                left join (
                    -- Input quantity
                    select
                        q.product_id,
                        sum(q.qty) as qty
                    from stock_quant as q
                    left join stock_location as l on l.id=q.location_id
                    where l.name='Input'
                    group by q.product_id
                ) as i on i.product_id=m.product_id
                left join (
                    -- Stock quantity
                    select
                        q.product_id,
                        sum(q.qty) as qty
                    from stock_quant as q
                    left join stock_location as l on l.id=q.location_id
                    where l.name='Stock'
                    group by q.product_id
                ) as s on s.product_id=m.product_id
                left join (
                    -- stock reservation quantity
                    select
                        q.product_id,
                        sum(q.qty) as res_qty,
                        string_agg(m.origin, ', ') as res_names
                    from stock_quant as q
                    left join stock_move as m on m.id=q.reservation_id
                    left join stock_location as l on l.id=q.location_id
                    where l.name='Stock'
                    and reservation_id is not null
                    group by q.product_id
                ) as res on res.product_id=m.product_id
                order by m.sequence
            )
        """)
