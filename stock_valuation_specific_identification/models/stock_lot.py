# Copyright 2024 Matt Taylor
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.tools import float_is_zero


class StockLot(models.Model):
    _inherit = 'stock.lot'

    stock_move_line_ids = fields.One2many(
        comodel_name="stock.move.line",
        inverse_name="lot_id",
    )
    company_currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Valuation Currency',
        compute='_compute_value_svl',
        compute_sudo=True,
        help="Technical field to correctly show the currently selected "
             "company's currency that corresponds to the totaled value of the "
             "product's valuation layers")
    value_svl = fields.Float(
        compute="_compute_value",
        compute_sudo=True,
    )
    quantity_svl = fields.Float(
        compute="_compute_value",
        compute_sudo=True,
    )
    unit_value_svl = fields.Monetary(
        compute="_compute_value",
        compute_sudo=True,
        currency_field="company_currency_id",
    )

    @api.depends("stock_move_line_ids")
    @api.depends_context("company")
    def _compute_value(self):
        company_id = self.env.company
        self.company_currency_id = company_id.currency_id
        for rec in self:
            rec.value_svl = sum(rec.stock_move_line_ids.mapped('value_remaining'))
            rec.quantity_svl = sum(rec.stock_move_line_ids.mapped('qty_remaining'))
            if not float_is_zero(
                rec.quantity_svl,
                precision_rounding=rec.product_id.uom_id.rounding
            ):
                rec.unit_value_svl = rec.value_svl / rec.quantity_svl
            else:
                rec.unit_value_svl = 0.0
