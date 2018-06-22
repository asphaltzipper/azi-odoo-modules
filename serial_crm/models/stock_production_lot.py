# -*- coding: utf-8 -*-

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
        comodel_name='mrp.repair',
        inverse_name='lot_id',
        string='Repairs')

    reval_ids = fields.One2many(
        comodel_name='stock.lot.revaluations',
        inverse_name='lot_id',
        string='Revaluation line quants')

    state = fields.Selection(
        selection=[
            ('assigned', 'Assigned'),
            ('internal', 'Inventory'),
            ('production', 'WIP'),
            ('customer', 'Shipped'),
            ('inventory', 'Lost/Scrapped'),
            ('lot', 'Lot'),
        ],
        readonly=True,
        string='Status',
        compute='_compute_state',
        store=True,
        help="Assigned: product assigned, no stock moves\n"
             "Inventory: SERIAL moved to stock location\n"
             "WIP: SERIAL consumed in production location\n"
             "Shipped: SERIAL moved to customer location\n"
             "Lost/Scrapped: SERIAL moved to inventory loss or scrap location\n"
             "Lot: multi-unit lot")

    sale_order_ids = fields.Many2many(
        comodel_name='sale.order',
        string="Sale Orders")

    @api.depends('owner_ids')
    def _compute_current_owner(self):
        for lot in self:
            owners = lot.owner_ids.sorted(key=lambda r: r.owner_date, reverse=True)
            lot.partner_id = owners and owners[0].partner_id or False

    def get_next_serial(self):
        if not self.product_id:
            raise UserError(_("Product is required"))
        self.name = self.env['ir.sequence'].next_by_code('azi.fg.serial')

    @api.multi
    @api.depends('quant_ids.location_id')
    def _compute_state(self):
        for serial in self:
            if serial.product_id.tracking == 'lot':
                serial.state = 'lot'
                continue
            if not serial.quant_ids:
                serial.state = 'assigned'
                continue
            # sum quant_ids quantity, grouping by location
            # for serials, only one location can have a net quantity, and the quantity must be unity (1)
            # we sort locations by descending net quantity, and take the first record
            locs = serial.quant_ids.read_group(domain=[('lot_id', '=', serial.id)], fields=['location_id', 'qty'], groupby=['location_id'], orderby='qty desc')
            loc = self.env['stock.location'].browse(locs[0]['location_id'][0])
            serial.state = loc.usage
