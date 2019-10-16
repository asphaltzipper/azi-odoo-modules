# -*- coding: utf-8 -*-

import datetime
from odoo import fields, models, api


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    date_planned_start = fields.Datetime(
        string='Deadline Start',
        copy=False,
        default=fields.Datetime.now,
        index=True,
        required=True,
        oldname="date_planned",
        compute='_compute_date_planned_start',
        store=True)
    moves_plus = fields.One2many(
        comodel_name='production.move.analysis',
        inverse_name='raw_material_production_id',
        readonly=True
    )

    # require routings when creating manufacturing orders
    # I wish we could just do this:
    # routing_id = fields.Many2one(required=True)
    routing_id = fields.Many2one(
        comodel_name='mrp.routing',
        string='Routing',
        readonly=True,
        # required=True,
        compute='_compute_routing',
        store=True,
        help="The list of operations (list of work centers) to produce the finished product. The routing "
             "is mainly used to compute work center costs during operations and to plan future loads on "
             "work centers based on production planning.")

    @api.depends('date_planned_finished', 'product_id.produce_delay')
    def _compute_date_planned_start(self):
        for production in self:
            date_finished = datetime.datetime.strptime(production.date_planned_finished, '%Y-%m-%d %H:%M:%S')
            production.date_planned_start = date_finished - datetime.timedelta(
                days=int(production.product_id.produce_delay))

    @api.multi
    def write(self, vals):
        """Override wirte method to update stock move expected date that is related to mrp production"""
        res = super(MrpProduction, self).write(vals)
        if 'date_planned_finished' in vals:
            for record in self:
                moves = self.env['stock.move'].search(['|', ('raw_material_production_id', '=', record.id),
                                                       ('production_id', '=', record.id),
                                                       ('state', 'not in', ('cancel', 'done'))])
                moves.sudo().write({'date_expected': vals['date_planned_finished'],
                                    'date': vals['date_planned_finished']})
        return res
