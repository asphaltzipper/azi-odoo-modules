# Copyright 2020 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
import odoo.addons.decimal_precision as dp


class StockForecastDetailLine(models.TransientModel):
    _name = 'stock.forecast.detail.line'
    _description = 'Stock Detail Forecast Line'
    _order = 'product_id, tx_date, tx_type, product_qty desc, id'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        ondelete="cascade",
        index=True,
    )

    tx_type = fields.Selection(
        selection=[
            ('po', 'In PO'),
            ('rfq', 'In RFQ'),
            ('mo', 'In MO'),
            ('pick', 'Out Pick'),
            ('so', 'Out SO'),
            ('quote', 'Out Quotation'),
            ('ppo', 'In Planned PO'),
            ('pmo', 'In Planned MO'),
            ('ppick', 'Out Planned Pick'),
            ('pxfer', 'In Planned Transfer'),
            ('iphantom', 'In Phantom Move'),
            ('ophantom', 'Out Phantom Move'),
            ('ipmove', 'In Planned Move'),
        ],
        string='Tx Type',
        help="PO: Inbound from vendor\n"
             "RFQ: Potential inbound from vendor\n"
             "MO: Inbound from production\n"
             "Pick: Outbound to production\n"
             "SO: Outbound to customer\n"
             "Quotation: Potential outbound to customer\n"
             "Planned PO: Planned inbound from vendor\n"
             "Planned MO: Planned inbound from production\n"
             "Planned Pick: Planned outbound to production\n"
             "Planned Transfer: Planned move from another location\n"
             "Planned Move: Planned move of unknown type",
    )

    tx_date = fields.Date(
        string="Date",
        required=True,
        help="Scheduled completion date for the transaction",
    )

    product_qty = fields.Float(
        string="Tx Qty",
        digits=dp.get_precision('Product Unit of Measure'),
        required=True,
        help="Qty=1 is implied for schedule lines, Qty<0 when qty out.",
    )

    before_qty = fields.Float(
        string="Before",
        digits=dp.get_precision('Product Unit of Measure'),
        required=True,
        default=0.0,
        help="The cumulative quantity or running sum of transactions",
    )

    after_qty = fields.Float(
        string="After",
        digits=dp.get_precision('Product Unit of Measure'),
        required=True,
        default=0.0,
        help="The cumulative quantity or running sum of transactions",
    )

    late = fields.Boolean(
        string='Late',
    )

    status = fields.Selection(
        selection=[('actual', 'Actual'), ('planned', 'Planned')],
        string='Status',
        help="Schedule lines and material plan items are planned, only"
        " schedule lines with no confirmed SO or MO included.",
    )

    origin = fields.Char('Source')
