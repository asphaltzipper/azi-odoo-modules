from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class SaleWarranty(models.Model):
    _name = 'sale.warranty'
    _description = 'Warranty'
    _inherit = ['mail.thread']
    _order = 'start_date desc'

    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        required=True,
    )
    warranty_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Type',
        required=True,
        domain=[('is_warranty', '=', True)],
    )
    units = fields.Selection(
        related='warranty_product_id.warranty_units',
        string='Units',
        readonly=True,
        store=True,
    )
    duration = fields.Integer(
        related='warranty_product_id.warranty_duration',
        string='Duration',
        readonly=True,
        store=True,
    )
    description_sale = fields.Text(
        related='warranty_product_id.description_sale',
        string='Description',
        readonly=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
    )
    lot_tracking = fields.Selection(
        related='product_id.tracking',
    )
    lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Serial',
    )
    move_line_id = fields.Many2one(
        comodel_name='stock.move.line',
        string='Move Line',
    )
    move_id = fields.Many2one(
        related='move_line_id.move_id',
    )
    picking_id = fields.Many2one(
        related='move_line_id.move_id.picking_id',
    )
    sale_id = fields.Many2one(
        related='move_line_id.move_id.picking_id.sale_id',
    )
    start_date = fields.Date(
        string='Start Date',
        required=True,
        default=fields.Date.today(),
    )
    cancel_date = fields.Date(
        string='Cancel Date',
    )
    expire_date = fields.Date(
        string='Expire Date',
        compute='_compute_expire_date',
        store=True,
        compute_sudo = True,
    )
    expired = fields.Boolean(
        string='Is Expired',
        compute='_compute_expired',
        compute_sudo=True,
    )

    @api.constrains('lot_id', 'product_id')
    def _validate_lot_id(self):
        if self.product_id and self.lot_tracking != 'none' and not self.lot_id:
            raise ValidationError(_(
                'Serial number is required for product %s',
                self.product_id.default_code,
            ))
        if self.product_id and self.lot_id and self.lot_id.product_id != self.product_id:
            raise ValidationError(_(
                "Serial number %s has product %s, which is different from %s",
                self.lot_id.name,
                self.lot_id.product_id.default_code,
                self.product_id.default_code,
            ))

    @api.depends('product_id', 'lot_id', 'partner_id', 'expire_date')
    def _compute_name(self):
        for rec in self:
            rec.name = _(
                "%s, %s, %s",
                rec.lot_id.name or rec.product_id.default_code,
                rec.expire_date.strftime('%Y-%m-%d'),
                rec.partner_id.name,
            )

    @api.depends('start_date', 'cancel_date', 'units', 'duration')
    def _compute_expire_date(self):
        for rec in self:
            if rec.cancel_date:
                rec.expire_date = rec.cancel_date
            else:
                unit_key = {'day': 'days', 'month': 'months', 'year': 'years'}.get(rec.units)
                delta = relativedelta(**{unit_key: rec.duration}) if unit_key else relativedelta()
                rec.expire_date = rec.start_date + delta

    @api.depends('expire_date')
    def _compute_expired(self):
        for rec in self:
            rec.expired = (rec.expire_date < fields.Date.today())
