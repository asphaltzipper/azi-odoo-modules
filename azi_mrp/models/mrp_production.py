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

    @api.depends('date_planned_finished', 'product_id.produce_delay')
    def _compute_date_planned_start(self):
        for production in self:
            production.date_planned_start = production.date_planned_finished - datetime.timedelta(
                days=int(production.product_id.produce_delay))

    # select *
    # from mrp_bom as b
    # left join product_template as t on t.id=b.product_tmpl_id
    # where b.routing_id is null
    # and t.deprecated=false
    # and b.type='normal'
    # and b.product_id in (

    @api.multi
    def write(self, vals):
        """Override wirte method to update stock move expected date that is related to mrp production"""
        res = super(MrpProduction, self).write(vals)
        if 'date_planned_finished' in vals or 'date_planned_start' in vals:
            for record in self:
                date_planned_start = 'date_planned_start' in vals and vals['date_planned_start'] or record.date_planned_start
                moves = self.env['stock.move'].search(['|', ('raw_material_production_id', '=', record.id),
                                                       ('production_id', '=', record.id),
                                                       ('state', 'not in', ('cancel', 'done'))])
                moves.sudo().write({'date_expected': date_planned_start,
                                    'date': date_planned_start})
                move_lines = moves.mapped('move_line_ids')
                move_lines and move_lines.sudo().write({'date': date_planned_start})
        return res
