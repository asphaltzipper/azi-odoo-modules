from odoo import models, fields, api
from odoo.exceptions import UserError


class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    document_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        domain=[('res_model', '=', 'stock.production.lot'), ('type', '=', 'binary')],
        auto_join=True,
        string="Documents")

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        ondelete='set null',
        compute='_compute_current_owner',
        store=True)

    owner_ids = fields.One2many(
        comodel_name='stock.lot.partner',
        inverse_name='lot_id',
        string='Owners')

    note_ids = fields.One2many(
        comodel_name='stock.lot.note',
        inverse_name='lot_id',
        string='Notes')

    description = fields.Text(string="Description")

    change_ids = fields.One2many(
        comodel_name='stock.lot.change',
        inverse_name='parent_lot_id',
        string='Changes')

    repair_ids = fields.One2many(
        comodel_name='repair.order',
        inverse_name='lot_id',
        string='Repairs')

    reval_ids = fields.One2many(
        comodel_name='stock.lot.revaluations',
        inverse_name='lot_id',
        string='Revaluation lines')

    move_line_ids = fields.One2many(
        comodel_name='stock.move.line',
        inverse_name='lot_id',
        string='Moves',
        readonly=True,
        domain=[('state', '=', 'done')],
    )

    state = fields.Selection(
        selection=[
            ('assigned', 'Assigned'),
            ('internal', 'Inventory'),
            ('production', 'WIP'),
            ('customer', 'Shipped'),
            ('inventory', 'Lost/Scrapped'),
            ('lot', 'Lot'),
            ('supplier', 'Supplier'),
            ('procurement', 'Procurement'),
            ('transit', 'Transit'),
        ],
        readonly=True,
        string='Status',
        compute='_compute_state',
        # store=True,
        help="Assigned: product assigned, no stock moves\n"
             "Inventory: SERIAL moved to stock location\n"
             "WIP: SERIAL consumed in production location\n"
             "Shipped: SERIAL moved to customer location\n"
             "Lost/Scrapped: SERIAL moved to inventory loss or scrap location\n"
             "Lot: multi-unit lot")

    sale_order_ids = fields.Many2many(
        comodel_name='sale.order',
        string="Sale Orders")

    current_hours = fields.Float(
        compute='_compute_current_hours',
        string='Total Hours')

    hour_ids = fields.One2many(
         comodel_name='stock.lot.hour.log',
         inverse_name='lot_id',
         string='Hours')

    @api.depends('owner_ids')
    def _compute_current_owner(self):
        for lot in self:
            owners = lot.owner_ids.sorted(key=lambda r: r.owner_date, reverse=True)
            lot.partner_id = owners and owners[0].partner_id or False

    @api.depends('hour_ids')
    def _compute_current_hours(self):
        for lot in self:
            if len(lot.hour_ids):
                lot.current_hours = lot.hour_ids.sorted(lambda x: x.date, reverse=True)[0].hours

    def get_next_serial(self):
        if not self.product_id:
            raise UserError(_("Product is required"))
        self.name = self.env['ir.sequence'].next_by_code('azi.fg.serial')

    @api.multi
    @api.depends('move_line_ids')
    def _compute_state(self):
        for serial in self:
            if serial.product_id.tracking == 'lot':
                serial.state = 'lot'
                continue
            moves_in_out = serial.move_line_ids.filtered(
                lambda x: x.state == 'done' and
                          (x.location_id.usage == 'internal' and
                           x.location_dest_id.usage != 'internal') or
                          (x.location_id.usage != 'internal' and
                           x.location_dest_id.usage == 'internal')
            )
            if not moves_in_out:
                serial.state = 'assigned'
                continue
            last_move = moves_in_out.sorted(lambda x: x.date)[-1]
            serial.state = last_move.location_dest_id.usage
