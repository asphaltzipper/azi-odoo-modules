# -*- coding: utf-8 -*-


from odoo import api, fields, models, tools
from odoo.addons import decimal_precision as dp


class ProductionMoveAnalysis(models.Model):
    _name = 'production.move.analysis'
    _auto = False

    # these fields selected from the database view
    raw_material_production_id = fields.Many2one(
        'mrp.production', 'Production Order for raw materials')
    production_id = fields.Many2one('mrp.production', 'Production Order')
    date = fields.Datetime(
        'Date', default=fields.Datetime.now, index=True, required=True,
        help="Move date: scheduled date until move is done, then date of actual move processing")
    date_expected = fields.Datetime(
        'Expected', default=fields.Datetime.now, index=True, required=True)
    picking_id = fields.Many2one('stock.picking', 'Transfer Reference', index=True, states={'done': [('readonly', True)]})
    sequence = fields.Integer('Sequence', default=10)
    origin = fields.Char("Source Document")
    product_id = fields.Many2one(
        'product.product', 'Product',
        domain=[('type', 'in', ['product', 'consu'])], index=True, required=True,
        states={'done': [('readonly', True)]})
    product_uom_qty = fields.Float(
        'Quantity',
        digits=dp.get_precision('Product Unit of Measure'),
        default=1.0, required=True, states={'done': [('readonly', True)]},
        help="This is the quantity of products from an inventory "
             "point of view. For moves in the state 'done', this is the "
             "quantity of products that were actually moved. For other "
             "moves, this is the quantity of product that is planned to "
             "be moved. Lowering this quantity does not generate a "
             "backorder. Changing this quantity on assigned moves affects "
             "the product reservation, and should be done with care.")
    product_uom = fields.Many2one(
        'product.uom', 'Unit of Measure', required=True, states={'done': [('readonly', True)]})
    # TDE FIXME: make it stored, otherwise group will not work
    location_id = fields.Many2one(
        'stock.location', 'Source Location',
        auto_join=True, index=True, required=True, states={'done': [('readonly', True)]},
        help="Sets a location if you produce at a fixed location. This can be a partner location if you subcontract the manufacturing operations.")
    location_dest_id = fields.Many2one(
        'stock.location', 'Destination Location',
        auto_join=True, index=True, required=True, states={'done': [('readonly', True)]},
        help="Location where the system will stock the finished products.")
    create_date = fields.Datetime('Creation Date', index=True, readonly=True)
    state = fields.Selection([
        ('draft', 'New'), ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Move'), ('confirmed', 'Waiting Availability'),
        ('assigned', 'Available'), ('done', 'Done')], string='Status',
        copy=False, default='draft', index=True, readonly=True,
        help="* New: When the stock move is created and not yet confirmed.\n"
             "* Waiting Another Move: This state can be seen when a move is waiting for another one, for example in a chained flow.\n"
             "* Waiting Availability: This state is reached when the procurement resolution is not straight forward. It may need the scheduler to run, a component to be manufactured...\n"
             "* Available: When products are reserved, it is set to \'Available\'.\n"
             "* Done: When the shipment is processed, the state is \'Done\'.")
    tracking = fields.Char(
        string="Tracking",
        default='none',
        required=True)
    product_type = fields.Selection(
        # selection=dict(self.env['product.template'].fields_get(allfields=['type'])['type']['selection'])['key'],
        selection=[
            ('product', 'Stockable'),
            ('consu', 'Consumable'),
            ('service', 'Service')],
        string='Product Type',
        required=True)
    route_names = fields.Char(
        string='Route',)
    input_qty = fields.Float(
        string='Input Quantity')
    stock_qty = fields.Float(
        string='Stock Quantity')
    res_qty = fields.Float(
        string='Reserved')
    avail_qty = fields.Float(
        string='Available',
        help='Stock quantity, minus quantity reserved anywhere, plus quantity reserved to this stock move')
    assigned_qty = fields.Float(
        string='Assigned',
        readonly=True,
        help='Quantity that has already been reserved for this move')
    res_names = fields.Char(
        string='Reservations',)
    e_kanban = fields.Boolean(
        string='E-Kanban',
        default=False,
        help="Material planning (MRP) for This product will be handled by electronic kanban")
    default_proc_qty = fields.Float(
        string='Kanban Qty',
        help="Default procurement quantity for electronic kanban ordering")

    def action_material_analysis(self):
        self.ensure_one()
        return self.product_id.action_material_analysis()

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'production_move_analysis')
        self._cr.execute("""
            CREATE VIEW production_move_analysis AS (
                select
                    m.id,
                    m.raw_material_production_id,
                    m.production_id,
                    m.date,
                    m.date_expected,
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
                    p.e_kanban,
                    p.default_proc_qty,
                    t.tracking,
                    t.type as product_type,
                    r.route_names,
                    i.qty as input_qty,
                    s.qty as stock_qty,
                    res.res_qty,
                    res.res_names,
                    case
                        when t.type = 'consu'
                        then m.product_uom_qty
                        else coalesce(a.res_qty, 0.0)
                        end as assigned_qty,
                    case
                        when t.type = 'consu'
                        then coalesce(res.res_qty, a.res_qty, m.product_uom_qty, 0.0)
                        else coalesce(s.qty, 0.0) - coalesce(res.res_qty, 0.0) + coalesce(a.res_qty, 0.0)
                        end as avail_qty
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
                left join (
                    -- this reservation quantity
                    select
                    q.product_id,
                    q.reservation_id,
                    sum(q.qty) as res_qty
                    from stock_quant as q
                    where reservation_id is not null
                    group by q.product_id, q.reservation_id
                ) as a on a.product_id=m.product_id and a.reservation_id=m.id
                order by m.sequence
            )
        """)
