# Copyright 2020 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, ValidationError


class MrpPlannedPickKit(models.TransientModel):
    _name = 'mrp.planned.pick.kit'
    _description = 'MRP Planned Pick Kit'
    _order = 'product_id'

    user_id = fields.Many2one(
        comodel_name='res.users',
        string="User",
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        readonly=True,
        ondelete='cascade',
    )
    product_qty = fields.Float(
        string="Produce Qty",
        required=True,
        digits=dp.get_precision('Product Unit of Measure'),
    )
    state = fields.Selection(
        selection=[
            ('new', 'New'),
            ('done', 'Done'),
        ],
        default='new',
        required=True,
    )
    routing_detail = fields.Char(
        string="Route",
        compute="_compute_routing_detail",
    )
    no_batch = fields.Boolean(
        string="No Batch",
        compute="_compute_no_batch",
    )
    line_ids = fields.One2many(
        comodel_name='mrp.planned.pick.kit.line',
        inverse_name='kit_id',
        string="Lines",
    )
    show_images = fields.Boolean(
        string="Show Images",
        required=True,
        default=True,
    )
    location_id = fields.Many2one(
        comodel_name='stock.location'
    )
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
    )

    @api.onchange('product_qty')
    def _onchange_product_qty(self):
        for line in self.line_ids:
            line.product_qty = line.factor * self.product_qty

    @api.model
    @api.depends('product_id')
    def _compute_routing_detail(self):
        for rec in self:
            bom = rec.product_id.bom_ids and rec.product_id.bom_ids[0]
            if bom:
                rec.routing_detail = ", ".join(
                    [x for x in bom.routing_id.operation_ids.mapped('workcenter_id.code') if x])

    @api.model
    @api.depends('product_id')
    def _compute_no_batch(self):
        for rec in self:
            rec.no_batch = rec.product_id.mrp_area_ids[0].mrp_nbr_days == 0

    @api.constrains('product_qty', 'no_batch')
    def _check_no_batch_quantity(self):
        if self.no_batch and self.product_qty > 1.0:
            raise ValidationError(_("This product cannot be produced in batches. Set the kit quantity to 1.0"))
        return True

    @api.multi
    def action_toggle_images(self):
        self.ensure_one()
        if self.show_images:
            self.show_images = False
        else:
            self.show_images = True

    @api.multi
    def action_done(self):
        self.ensure_one()
        if self.state == 'done':
            raise UserError(_("This kit is already done. Start a new one"))
        self.product_id.mfg_kit_qty += self.product_qty
        self.write({'state': 'done'})


class MrpPlannedPickKitLine(models.TransientModel):
    _name = 'mrp.planned.pick.kit.line'
    _description = 'MRP Planned Pick Kit Line'
    _order = 'product_id'

    kit_id = fields.Many2one(
        comodel_name='mrp.planned.pick.kit',
        readonly=True,
        ondelete='cascade'
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        readonly=True,
        ondelete='cascade',
    )
    routing_detail = fields.Char(
        string="Route",
        compute="_compute_routing_detail",
        store=True,
    )
    image_small = fields.Binary(
        related='product_id.image_small',
        string='Image',
    )
    type = fields.Selection(
        related='product_id.type',
    )
    supply_method = fields.Selection(
        selection=[('buy', 'Buy'),
                   ('none', 'Undefined'),
                   ('manufacture', 'Produce'),
                   ('phantom', 'Kit'),
                   ('pull', 'Pull From'),
                   ('push', 'Push To'),
                   ('pull_push', 'Pull & Push')],
        string='Supply Method',
        compute='_compute_supply_method',
        store=True,
    )
    product_qty = fields.Float(
        string="Required",
        digits=dp.get_precision('Product Unit of Measure'),
    )
    factor = fields.Float(
        string="Factor",
        readonly=True,
    )
    onhand_qty = fields.Float(
        string="On Hand",
        compute="_compute_available_qty",
        store=True,
        digits=dp.get_precision('Product Unit of Measure'),
    )
    reserved_qty = fields.Float(
        string="Reserved",
        compute="_compute_available_qty",
        store=True,
        digits=dp.get_precision('Product Unit of Measure'),
    )
    available_qty = fields.Float(
        string="Available",
        compute="_compute_available_qty",
        store=True,
        digits=dp.get_precision('Product Unit of Measure'),
        help="On-Hand quantity less Reserved quantity",
    )
    short = fields.Boolean(
        string="Short",
        compute="_compute_available_qty",
        store=True,
    )
    show_images = fields.Boolean(
        related='kit_id.show_images',
    )
    location_id = fields.Many2one(
        related='kit_id.location_id',
    )
    warehouse_id = fields.Many2one(
        related='kit_id.warehouse_id',
    )
    kanban_item = fields.Boolean(
        string="Kanban",
        related='product_id.e_kanban_verified',
    )

    @api.multi
    @api.depends('product_id', 'location_id', 'warehouse_id')
    def _compute_supply_method(self):
        group_obj = self.env['procurement.group']
        for rec in self:
            values = {
                'warehouse_id': rec.warehouse_id,
                'company_id': self.env.user.company_id.id,
                # TODO: better way to get company
            }
            rule = group_obj._get_rule(rec.product_id, rec.location_id, values)
            if rule.action == 'manufacture' and \
                    rec.product_id.product_tmpl_id.bom_ids and \
                    rec.product_id.product_tmpl_id.bom_ids[0].type == 'phantom':
                rec.supply_method = 'phantom'
            else:
                rec.supply_method = rule.action if rule else 'none'

    @api.model
    @api.depends('kit_id.product_qty', 'product_id')
    def _compute_available_qty(self):
        for rec in self:
            if rec.product_id.type == 'product':
                on_hand = rec.product_id.qty_available
                rec.reserved_qty = sum(
                    rec.product_id.stock_move_ids.mapped('reserved_availability')
                )
                rec.onhand_qty = on_hand
                rec.available_qty = on_hand - rec.reserved_qty
                rec.short = rec.available_qty < rec.product_qty
            else:
                rec.onhand_qty = rec.product_qty + 1
                rec.reserved_qty = 0.0
                rec.available_qty = rec.product_qty + 1
                rec.short_qty = False

    @api.model
    @api.depends('product_id')
    def _compute_routing_detail(self):
        for rec in self:
            bom = rec.product_id.bom_ids and rec.product_id.bom_ids[0]
            if bom and bom.routing_id:
                rec.routing_detail = ", ".join(
                    [x for x in bom.routing_id.operation_ids.mapped('workcenter_id.code') if x])
