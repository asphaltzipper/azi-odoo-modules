# -*- coding: utf-8 -*-
# (c) 2016 Matt Taylor
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models, _
from odoo.exceptions import UserError


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
                line.copy(default)
        return record


class MrpScheduleLine(models.Model):
    _name = "mrp.schedule.line"
    _description = "Master Schedule Line"

    name = fields.Char(
        string='BuildID',
        required=True,
        index=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('mrp.schedule.line'),
        readonly=True)

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
        ondelete="restrict")

    production_id = fields.Many2one(
        comodel_name='mrp.production',
        string='MfgOrder',
        index=True,
        ondelete='set null')

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
        ondelete='set null')

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
        return True if not self.production_id or (self.production_id and
                                                  self.production_id.state not
                                                  in 'done') else False

    @api.multi
    def copy(self, default=None):
        # schedule_id is set by MrpSchedule copy() so skip double check of
        # production state
        if (default.get('schedule_id') or
                self.check_production_state_not_done()):
            return super(MrpScheduleLine, self).copy(default)
        else:
            raise UserError(_("Duplicating a Schedule Line linked to a"
                              " Completed MfgOrder is not allowed."))

    def get_next_serial(self):
        if not self.product_id:
            raise UserError(_("Product is required"))
        self.lot_id = self.env['stock.production.lot'].create({
            'name': self.env['ir.sequence'].next_by_code('azi.fg.serial'),
            'product_id': self.product_id.id
        })
