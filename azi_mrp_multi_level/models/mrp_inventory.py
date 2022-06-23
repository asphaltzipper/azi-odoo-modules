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
    routing_detail = fields.Char(
        string='Routing Detail',
        compute='_compute_routing_detail',
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

    @api.depends('product_id')
    def _compute_routing_detail(self):
        for record in self:
            if record.product_id:
                operations = self.env['mrp.bom'].search([('product_id', '=', record.product_id.id)]).\
                    mapped('routing_id.operation_ids')
                if operations:
                    work_center_codes = [code for code in operations.mapped('workcenter_id.code') if code]
                    record.routing_detail = ", ".join(work_center_codes)

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
