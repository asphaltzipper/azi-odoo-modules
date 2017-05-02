# -*- coding: utf-8 -*-
# Copyright 2017 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.addons import decimal_precision as dp


class MrpMaterialAnalysisLine(models.TransientModel):
    _name = 'mrp.material.analysis.line'
    _description = 'Material Requirements Planning'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        ondelete="no action",
        index=True,
        help="Product with incomplete transaction.")

    tx_type = fields.Selection(
        selection=[('po', 'PO'), ('mo', 'MO'), ('pick', 'Pick'), ('so', 'SO'),
                   ('ppo', 'Planned PO'), ('pmo', 'Planned MO'),
                   ('ppick', 'Planned Pick')],
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

    product_qty = fields.Float(
        string="Qty",
        digits=dp.get_precision('Product Unit of Measure'),
        required=True,
        help="Qty=1 is implied for schedule lines, Qty<0 when qty out.")

    late = fields.Boolean(
        string='Late',
        help="Incomplete transaction beyond completion date.")

    status = fields.Selection(
        selection=[('actual', 'Actual'), ('planned', 'Planned')],
        string='Status',
        help="Schedule lines and material plan items are planned, only"
        " schedule lines with no confirmed SO or MO included.")

    production_id = fields.Many2one(
        comodel_name='mrp.production',
        string='Manufacturing Order',
        index=True,
        store=True)

    pick_id = fields.Many2one(
        comodel_name='stock.move',
        related='production_id.move_raw_ids',
        string='Pick',
        index=True,
        store=True)

    sale_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        index=True,
        store=True)

    purchase_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Purchase Order',
        index=True,
        store=True)

    schedule_line_id = fields.Many2one(
        comodel_name='schedule.line',
        string='Schedule Line',
        index=True,
        store=True)

    material_plan_id = fields.Many2one(
        comodel_name='mrp.material.plan',
        string='Material Plan',
        index=True,
        store=True)
