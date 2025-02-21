from odoo import models, fields, api


class MrpInventory(models.Model):
    _inherit = 'mrp.inventory'

    e_kanban = fields.Boolean(
        related='product_id.e_kanban',
        store=True,
    )
    deprecated = fields.Boolean(
        related='product_id.deprecated',
        string="Obsolete",
        store=True,
    )
    routing_name = fields.Char(
        related='product_id.routing_name',
        store=True,
    )
    main_supplier_id = fields.Many2one(
        comodel_name='res.partner',
        string='Vendor',
        related='product_mrp_area_id.main_supplier_id',
        store=True,
    )
    on_blanket = fields.Boolean(
        string='Blanket',
        compute='_compute_on_blanket',
        store=True,
    )
    to_expedite = fields.Boolean(
        string='Expedite',
        required=True,
        default=False,
    )
    time_cycle = fields.Float(
        string='Hours',
        compute="_compute_workorder_time",
        store=True,
    )
    workorder_count = fields.Integer(
        string="# Work Orders",
        compute="_compute_workorder_time",
        store=True,
    )

    @api.depends('product_id')
    def _compute_on_blanket(self):
        buy_id = self.env.ref('purchase_stock.route_warehouse0_buy').id
        blanket_orders = self.env['purchase.requisition'].search([
            ('state', 'in', ['ongoing', 'in_progress', 'open']),
            ('type_id', '=', self.env.ref('purchase_requisition.type_single').id),
        ])
        blanket_products = self.env['purchase.requisition.line'].search(
            [('requisition_id', 'in', blanket_orders.ids)]).mapped('product_id')
        for record in self:
            if buy_id in record.product_id.route_ids.ids and \
                    record.product_id in blanket_products:
                record.on_blanket = True
            else:
                record.on_blanket = False

    @api.depends('product_id')
    def _compute_workorder_time(self):
        make_lines = self.filtered(lambda x: x.supply_method=="manufacture" and x.to_procure>0)
        other_lines = self - make_lines
        other_lines.update({"time_cycle": 0, "workorder_count": 0})
        boms_by_product = self.env["mrp.bom"]._bom_find(make_lines.mapped("product_id"))
        for rec in self:
            bom = boms_by_product.get(rec.product_id, self.env["mrp.bom"])
            if not bom:
                rec.time_cycle = 0
                rec.workorder_count = 0
                continue
            if not bom.operation_ids:
                rec.time_cycle = 0
                rec.workorder_count = 0
                continue
            rec.time_cycle = sum(bom.mapped("operation_ids.time_cycle"))/60
            rec.workorder_count = sum(bom.mapped("operation_ids.workorder_count"))
