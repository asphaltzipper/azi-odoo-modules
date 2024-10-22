# Copyright 2024 Matt Taylor
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class StockValuationLayerRevaluation(models.TransientModel):
    _inherit = 'stock.valuation.layer.revaluation'

    @api.model
    def default_get(self, default_fields):
        res = super().default_get(default_fields)
        if res.get("lot_id"):
            lot = self.env["stock.lot"].browse(res["lot_id"])
            if lot.quantity_svl <= 0:
                raise UserError(
                    _("We cannot revalue a lot with an empty or negative stock.")
                )
        return res

    lot_id = fields.Many2one(
        comodel_name="stock.lot",
        string="Related Lot",
    )
    current_lot_value_svl = fields.Float(
        string="Current Lot Value",
        compute="_compute_lot_value",
    )
    current_lot_quantity_svl = fields.Float(
        string="Current Lot Quantity",
        compute="_compute_lot_value",
    )
    new_lot_value = fields.Monetary(
        string="New value",
        compute='_compute_lot_value',
    )
    new_lot_value_by_qty = fields.Monetary(
        string="New value by quantity",
        compute='_compute_lot_value',
    )

    @api.depends('product_id', 'lot_id', 'added_value')
    def _compute_lot_value(self):
        for reval in self:
            if (
                reval.lot_id
                and reval.product_id.tracking != 'none'
                and reval.product_id.categ_id.property_cost_method == 'fifo'
            ):
                reval.current_lot_value_svl = reval.lot_id.value_svl
                reval.current_lot_quantity_svl = reval.lot_id.quantity_svl
                reval.new_lot_value = reval.current_lot_value_svl + reval.added_value
                if not float_is_zero(
                    reval.current_lot_quantity_svl,
                    precision_rounding=reval.product_id.uom_id.rounding
                ):
                    reval.new_lot_value_by_qty = reval.new_lot_value / reval.current_lot_quantity_svl
                else:
                    reval.new_lot_value_by_qty = 0.0
            else:
                reval.current_lot_value_svl = 0.0
                reval.current_lot_quantity_svl = 0.0
                reval.new_lot_value = 0.0
                reval.new_lot_value_by_qty = 0.0

    def _get_revaluation_remaining_svls(self):
        svls = super(StockValuationLayerRevaluation,
                     self)._get_revaluation_remaining_svls()
        if self.lot_id:
            svls = svls.filtered(lambda x: self.lot_id in x.lot_ids)
            if len(svls) > 1:
                raise UserError(
                    _("Found multiple valuation layers for lot %s", self.lot_id.name)
                )
            if len(svls.mapped("lot_ids")) > 1:
                raise UserError(
                    _(
                        "Can't revalue layers with multiple lots: %s",
                        ", ".join(svls.mapped("lot_ids.name"))
                    )
                )
        return svls

    def _get_revaluation_svl_vals(self):
        vals = super(StockValuationLayerRevaluation, self)._get_revaluation_svl_vals()
        if self.lot_id:
            vals["lot_ids"] = [[6, 0, [self.lot_id.id]]]
        return vals

    def _create_revaluation_svl(self):
        res = super(StockValuationLayerRevaluation, self)._create_revaluation_svl()
        self.stock_valuation_layer_id = res
        return res


    def action_validate_revaluation(self):
        self.ensure_one()
        product_id = self.product_id.with_company(self.company_id)
        if (
            not self.lot_id
            and product_id.tracking != 'none'
            and product_id.categ_id.property_cost_method == 'fifo'
        ):
            raise UserError(
                _("Lot/Serial number is required for valuation of this product")
            )

        return super(StockValuationLayerRevaluation, self).action_validate_revaluation()
