from odoo import models, fields, _, api


class TsbSerial(models.Model):
    _name = 'tsb.serial'
    _description = 'Technical Service Bulletin Serialized Unit'
    _sql_constraints = [('bulletin_lot_unique', 'unique(bulletin_id,lot_id)', "Serial number must be unique per TSB")]

    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
    )
    bulletin_id = fields.Many2one(
        comodel_name='tsb.bulletin',
        string='TSB',
        required=True,
    )
    lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Serial',
        required=True,
    )
    start_date = fields.Date(
        related='bulletin_id.start_date',
        string='Start Date',
        store=True,
    )
    done_date = fields.Date(
        string='Completed Date',
    )
    is_done = fields.Boolean(
        string='Is Done',
        compute='_compute_is_done',
        store=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        related='lot_id.partner_id',
        string='Customer',
        store=True,
    )
    order_ids = fields.Many2many(
        comodel_name='sale.order',
        relation='tsb_serial_sale_order_rel',
        column1='tsb_serial_id',
        column2='sale_order_id',
        readonly=True,
        string='Sales Orders',
    )
    repair_ids = fields.Many2many(
        comodel_name='repair.order',
        relation='tsb_serial_repair_order_rel',
        column1='tsb_serial_id',
        column2='repair_order_id',
        readonly=True,
        string='Repair Orders',
    )

    @api.depends('lot_id', 'bulletin_id')
    def _compute_name(self):
        for rec in self:
            rec.name = _("%s - %s", rec.lot_id.name, rec.bulletin_id.name)

    @api.depends('done_date')
    def _compute_is_done(self):
        for rec in self:
            rec.is_done = rec.done_date or False
