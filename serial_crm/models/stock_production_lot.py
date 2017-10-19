# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'

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

    notes = fields.Text(string="Notes")

    change_ids = fields.One2many(
        comodel_name='stock.lot.change',
        inverse_name='parent_lot_id',
        string='Changes')

    repair_ids = fields.One2many(
        comodel_name='mrp.repair',
        inverse_name='lot_id',
        string='Repairs')

    state = fields.Selection(
        selection=[
            ('assigned', 'Assigned'),
            ('internal', 'Inventory'),
            ('production', 'WIP'),
            ('customer', 'Shipped'),
            ('inventory', 'Scrapped'),
            ('open', 'Open'),
            ('closed', 'Closed'),
        ],
        string='Status',
        required=True,
        default='assigned',
        help="Assigned: product assigned, no stock moves\n"
             "Inventory: SERIAL moved to stock location\n"
             "WIP: SERIAL consumed in production location\n"
             "Shipped: SERIAL moved to customer location\n"
             "Scrapped: SERIAL moved to scrap location\n"
             "Open: LOT open for transactions\n"
             "Open: LOT closed for transactions\n")

    @api.depends('owner_ids')
    def _compute_current_owner(self):
        for lot in self:
            owners = lot.owner_ids.sorted(key=lambda r: r.owner_date, reverse=True)
            lot.partner_id = owners and owners[0].partner_id or False
