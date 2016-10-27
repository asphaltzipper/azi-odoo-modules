# -*- coding: utf-8 -*-
# (c) 2016 Matt Taylor
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api, registry


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
        help='Reference identifier for integrating with external scheduling application.')

    @api.multi
    def action_release(self):
        domain = [('state', '=', 'released')]
        released_builds = self.env['mrp.schedule'].search(domain)
        for build in released_builds:
            build.state = 'superseded'
        for record in self:
            record.state = 'released'

    @api.multi
    def action_unrelease(self):
        for record in self:
            record.state = 'pending'


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

    notes = fields.Char(
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
        ondelete='cascade',
        readonly=True)

    state = fields.Selection(
        string="Schedule State",
        related='schedule_id.state',
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
