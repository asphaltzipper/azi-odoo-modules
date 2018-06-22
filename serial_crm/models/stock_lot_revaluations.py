# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
from odoo.addons import decimal_precision as dp


class StockLotRevaluations(models.Model):
    _name = 'stock.lot.revaluations'
    _auto = False

    # fields selected from the database view

    revaluation_id = fields.Many2one(
        comodel_name='stock.inventory.revaluation',
        string='Revaluation',
        readonly=True)

    quant_id = fields.Many2one(
        comodel_name='stock.quant',
        string='Quant',
        readonly=True)

    old_cost = fields.Float(
        string='Previous cost',
        readonly=True)

    new_cost = fields.Float(
        string='New Cost',
        digits=dp.get_precision('Product Price'),
        readonly=True)

    # fields related through the orm

    remarks = fields.Text(
        string='Remarks',
        related='revaluation_id.remarks',
        readonly=True)

    state = fields.Selection(
        selection=[('draft', 'Draft'),
                   ('posted', 'Posted'),
                   ('cancel', 'Cancelled')],
        string='Status',
        related='revaluation_id.state',
        readonly=True)

    lot_id = fields.Many2one(
        comodel_name='stock.production.lot',
        string="Serial",
        related='quant_id.lot_id',
        readonly=True)

    post_date = fields.Datetime(
        string='Posting Date',
        related='revaluation_id.post_date',
        readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'stock_lot_revaluations')
        self._cr.execute("""
            CREATE VIEW stock_lot_revaluations AS (
                select
                    l.id,
                    r.id as revaluation_id,
                    l.quant_id,
                    l.old_cost,
                    l.new_cost
                from stock_inventory_revaluation as r
                left join stock_inventory_revaluation_quant as l on l.revaluation_id=r.id
                order by r.post_date

            )
        """)
