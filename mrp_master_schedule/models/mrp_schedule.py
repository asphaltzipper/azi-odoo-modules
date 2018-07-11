# -*- coding: utf-8 -*-
# (c) 2016 Matt Taylor
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class MrpSchedule(models.Model):
    _name = "mrp.schedule"
    _description = "Master Schedule Header"

    name = fields.Char(
        string='Name',
        copy=False,
        required=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('mrp.schedule'))

    release_date = fields.Datetime(
        string='Release Date',
        readonly=True)

    state = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('released', 'Released'),
            ('superseded', 'Superseded')],
        string='Status',
        default='pending',
        help="Pending:    New schedule, will not used for MRP planning\n"
             "Released:   Schedule will be used for MRP planning. Older schedules will be marked Superseded.\n"
             "Superseded: A newer schedule has been released.")

    ext_ref = fields.Integer(
        string='ExternalID',
        index=True,
        readonly=True,
        copy=False,
        help='Reference identifier for integrating with external scheduling application.')

    line_ids = fields.One2many(
        comodel_name='mrp.schedule.line',
        inverse_name='schedule_id',
        string='Schedule Lines',
    )

    line_count = fields.Integer(
        "# Lines", compute='_compute_line_count')

    @api.multi
    def _compute_line_count(self):
        for schedule in self:
            schedule.line_count = len(schedule.line_ids)

    def get_released(self):
        domain = [('state', '=', 'released')]
        released = self.search(domain)
        return released

    @api.one
    def action_release(self):
        released = self.get_released()
        if released:
            released.state = 'superseded'
        self.release_date = fields.Datetime.now()
        self.state = 'released'

    @api.one
    def action_unrelease(self):
        self.release_date = False
        self.state = 'pending'

    @api.multi
    def do_view_schedule_lines(self):
        return self.env['mrp.schedule.line'].do_view_schedule_lines(False)

    @api.multi
    def copy(self, default=None):
        record = super(MrpSchedule, self).copy(default)
        default['schedule_id'] = record.id
        for line in self.line_ids:
            if line.check_production_state_not_done():
                line.copy({
                    'schedule_id': record.id,
                    'name': line.name,
                    'production_id': line.production_id.state != 'cancel' and line.production_id.id or False,
                    'sale_id': line.sale_id.state != 'cancel' and line.sale_id.id or False,
                    'lot_id': line.lot_id.id,
                })
        return record


class MrpScheduleLine(models.Model):
    _name = "mrp.schedule.line"
    _description = "Master Schedule Line"

    name = fields.Char(
        string='BuildID',
        required=True,
        index=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('mrp.schedule.line'),
        readonly=True,
        copy=False)

    description = fields.Char(
        string='Description',
        required=True)

    notes = fields.Text(
        string='Notes',
        help='To be replaced with some mail chatter feed thing')

    target_usage = fields.Selection(
        selection=[
            ('stock', 'Stock'),
            ('demo', 'Demo'),
            ('sale', 'Sale')],
        string='TargetUsage',
        required=True,
        default='stock')

    schedule_id = fields.Many2one(
        comodel_name='mrp.schedule',
        string='Schedule',
        required=True,
        ondelete='cascade',
        readonly=True,
        states={False: [('readonly', False)]}
    )

    state = fields.Selection(
        string="Schedule State",
        related='schedule_id.state',
        readonly=True,
        store=True
    )

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        ondelete='set null',
        readonly=True,
        states={'pending': [('readonly', False)]}
    )

    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        related='product_id.product_tmpl_id',
        string='ProdFamily',
        ondelete='set null',
        readonly=True,
        store=True,
        index=True)

    tracking = fields.Selection(
        related='product_id.tracking')

    lot_id = fields.Many2one(
        comodel_name='stock.production.lot',
        string='SerialNum',
        index=True,
        ondelete="restrict",
        copy=False)

    production_id = fields.Many2one(
        comodel_name='mrp.production',
        string='MfgOrder',
        index=True,
        ondelete='set null',
        copy=False)

    production_state = fields.Selection(
        string='MfgOrderState',
        readonly=True,
        related='production_id.state',
        help='State of the associated Manufacturing Order.')

    date_finish = fields.Date(
        string='CompletionDate',
        required=True,
        readonly=True,
        index=True,
        track_visibility='onchange',
        states={'pending': [('readonly', False)]},
        help='Planned date of completion for this build.')

    ext_ref = fields.Integer(
        string='ExternalID',
        index=True,
        readonly=True,
        help='Reference identifier for integrating with external scheduling application.')

    sale_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sales Order',
        index=True,
        ondelete='set null',
        copy=False)

    def write(self, vals):
        if vals.get('date_finish:week'):
            dt = fields.Date.from_string(self.date_finish)
            dtw = datetime.strptime(vals['date_finish:week'] + ' 1', "W%W %Y %w")
            vals['date_finish'] = dtw + relativedelta(days=dt.weekday())
        return super(MrpScheduleLine, self).write(vals)

    @api.multi
    def do_view_schedule_lines(self, change_domain=True):
        """
        This function returns an action that displays existing schedule lines
        of same schedule line of given id.
        """
        action = self.env.ref('mrp_master_schedule.do_view_schedule_lines').read()[0]
        if change_domain:
            action['domain'] = [('schedule_id', 'in', self.mapped('schedule_id').ids)]
        return action

    @api.model
    def check_production_state_not_done(self):
        if self.production_id and self.production_id.state == 'done':
            return False
        else:
            return True

    def get_next_serial(self):
        if self.lot_id:
            raise UserError(_("Must Delete existing Serial Number."))
        if not self.product_id:
            raise UserError(_("Product is required"))
        self.lot_id = self.env['stock.production.lot'].create({
            'name': self.env['ir.sequence'].next_by_code('azi.fg.serial'),
            'product_id': self.product_id.id
        })

    @api.model
    def create(self, vals):
        sched_id = vals.get('schedule_id') or self._context.get('default_schedule_id')
        if self.env['mrp.schedule'].browse(sched_id).state != 'pending':
            raise UserError(_("You can only create schedule lines for a pending schedule"))
        return super(MrpScheduleLine, self).create(vals)

    @api.multi
    def unlink(self):
        if any(x != 'pending' for x in self.mapped('schedule_id.state')):
            raise UserError(_("You can only delete schedule lines for a pending schedule"))
        return super(MrpScheduleLine, self).unlink()
