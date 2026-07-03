from odoo import api, models, fields, _


class StockRequestAbstract(models.AbstractModel):
    _inherit = 'stock.request.abstract'

    product_deprecated = fields.Boolean(
        related='product_id.deprecated',
        string='Obsolete',
        readonly=True,
        store=True)

    product_active = fields.Boolean(
        related='product_id.active',
        string='Product Active',
        readonly=True,
        store=True)

    product_responsible_id = fields.Many2one(
        related='product_id.responsible_id',
        readonly=True,
        store=True)

    product_type = fields.Selection(
        related='product_id.type',
        readonly=True,
        store=True)


class StockRequest(models.Model):
    _inherit = 'stock.request'

    other_purchase_ids = fields.One2many(
        comodel_name="purchase.order",
        compute="_compute_other_purchase_ids",
        compute_sudo=False,
        string="Other POs",
        readonly=True,
        help="These are open purchase orders, not created by this stock request",
    )
    has_other_pos = fields.Boolean(
        string="Has Other POs",
        compute="_compute_other_purchase_ids",
        compute_sudo=False,
        store=True,
    )
    other_production_ids = fields.One2many(
        comodel_name="mrp.production",
        compute="_compute_other_production_ids",
        compute_sudo=False,
        string="Other MOs",
        readonly=True,
        help="These are open manufacturing orders, not created by this stock request",
    )
    has_other_mos = fields.Boolean(
        string="Has Other MOs",
        compute="_compute_other_production_ids",
        compute_sudo=False,
        store=True,
    )

    def action_confirm(self):
        res = super(StockRequest, self).action_confirm()
        for record in self:
            if record.kanban_id and record.product_id.type == 'product':
                available_qty = record.product_id.qty_available
                other_kanbans = record.product_id.e_kanban_ids.filtered(lambda x: x.id != record.kanban_id.id)
                probable_qty = other_kanbans and sum(other_kanbans.mapped('product_uom_qty')) or 0
                if 0 <= available_qty <= probable_qty:
                    # available_qty may be more accurate than probable_qty when:
                    # - kanban scanned for a newly created product
                    # - kanban scanned after some additional product has already been consumed
                    continue
                location_id = record.kanban_id.location_id.id
                if probable_qty > 0:
                    stock_inventory = self.env['stock.inventory'].create({
                        'name': 'kanban order - %s' % record.product_id.name,
                        'product_selection': 'one',
                        'product_ids': [[6, False, [record.product_id.id]]],
                        'location_ids': [[6, False, [location_id]]]})

                    stock_inventory.action_state_to_in_progress()
                    stock_inventory.mapped("stock_quant_ids")[0].inventory_quantity = probable_qty
                    stock_inventory.mapped("stock_quant_ids")[0].action_apply_inventory()
                    stock_inventory.action_state_to_done()
        return res

    def _action_submit(self):
        for rec in self:
            if len(rec.route_ids) == 1:
                rec.route_id = rec.route_ids[0]
        super(StockRequest, self)._action_submit()

    @api.depends('product_id', 'purchase_line_ids', 'purchase_line_ids.state')
    def _compute_other_purchase_ids(self):
        for rec in self:
            rec.other_purchase_ids = self.env['stock.move'].search([
                ('state', 'not in', ['done', 'cancel']),
                ('product_id', '=', rec.product_id.id),
                ('purchase_line_id', 'not in', rec.purchase_line_ids.ids),
                ('purchase_line_id', '!=', False),
            ]).mapped('purchase_line_id.order_id')
            if rec.other_purchase_ids:
                rec.has_other_pos = True
            else:
                rec.has_other_pos = False

    @api.depends('product_id', 'production_ids', 'production_ids.state')
    def _compute_other_production_ids(self):
        for rec in self:
            rec.other_production_ids = self.env['mrp.production'].search([
                ('state', 'not in', ['done', 'cancel']),
                ('product_id', '=', rec.product_id.id),
                ('id', 'not in', rec.production_ids.ids),
            ])
            if rec.other_production_ids:
                rec.has_other_mos = True
            else:
                rec.has_other_mos = False
