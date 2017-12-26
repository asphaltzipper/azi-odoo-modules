# -*- coding: utf-8 -*-
# Copyright 2017 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
import odoo.addons.decimal_precision as dp


class MrpMaterialAnalysisLine(models.TransientModel):
    _name = 'mrp.material.analysis.line'
    _description = 'Material Requirements Planning'
    _order = 'product_id, tx_date, product_qty desc, id'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        ondelete="no action",
        index=True,
        help="Product with incomplete transaction.")

    tx_type = fields.Selection(
        selection=[
            ('po', 'PO'),
            ('rfq', 'RFQ'),
            ('mo', 'MO'),
            ('pick', 'Pick'),
            ('so', 'SO'),
            ('ppo', 'Planned PO'),
            ('pmo', 'Planned MO'),
            ('ppick', 'Planned Pick'),
        ],
        string='Tx Type',
        help="PO: Source Location Type = Vendor Location,"
        " MO: Source Location Type = Production"
        " Pick: Destination Location Type = Production"
        " (components consumed on an MO)"
        " SO: Destination Location Type = Customer Location"
        " Schedule Line"
        " Planned PO: move_type='supply', make=False"
        " Planned MO: move_type='supply', make=True"
        " Planned Pick: move_type='demand'")

    tx_date = fields.Date(
        string="Date",
        required=True,
        help="Scheduled completion date for the transaction")

    product_qty = fields.Float(
        string="Tx Qty",
        digits=dp.get_precision('Product Unit of Measure'),
        required=True,
        help="Qty=1 is implied for schedule lines, Qty<0 when qty out.")

    available_qty = fields.Float(
        string="Qty After",
        digits=dp.get_precision('Product Unit of Measure'),
        required=True,
        help="The cumulative quantity is the running sum of transactions")

    late = fields.Boolean(
        string='Late',
        help="Incomplete transaction beyond completion date.")

    status = fields.Selection(
        selection=[('actual', 'Actual'), ('planned', 'Planned')],
        string='Status',
        help="Schedule lines and material plan items are planned, only"
        " schedule lines with no confirmed SO or MO included.")

    origin = fields.Char('Source Document')
