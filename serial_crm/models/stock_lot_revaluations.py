from odoo import api, fields, models, tools
from odoo.addons import decimal_precision as dp


class StockLotRevaluations(models.Model):
    _name = 'stock.lot.revaluations'
    _auto = False
    _order = 'post_date'

    # fields selected from the database view

    revaluation_id = fields.Many2one(
        comodel_name='stock.inventory.revaluation',
        string='Revaluation',
        readonly=True)

    move_line_id = fields.Many2one(
        comodel_name='stock.move.line',
        string='Move',
        readonly=True)

    old_value = fields.Float(
        string='Previous Value',
        readonly=True)

    new_value = fields.Float(
        string='New Value',
        digits=dp.get_precision('Product Price'),
        readonly=True)

    post_date = fields.Date(
        string='Posting Date',
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
        related='move_line_id.lot_id',
        readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'stock_lot_revaluations')
        self._cr.execute("""
            CREATE VIEW stock_lot_revaluations AS (
                select
                    l.id,
                    r.id as revaluation_id,
                    ml.id as move_line_id,
                    l.old_value,
                    l.new_value,
                    r.post_date
                from stock_inventory_revaluation as r
                left join stock_inventory_revaluation_move as l on l.revaluation_id=r.id
                left join stock_move_line as ml on ml.move_id=l.move_id
            )
        """)
