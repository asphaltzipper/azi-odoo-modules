from odoo import models, fields, api, _


class StockLot(models.Model):
    _inherit = 'stock.lot'

    code128 = fields.Char(
        string="Code128 Encoded Name",
        compute="_compute_code128",
        store=True,
    )

    @api.depends('name')
    def _compute_code128(self):
        for lot in self:
            if not lot.name:
                lot.code128 = False
                continue
            lot.code128 = self.env['barcode.nomenclature'].get_code128_encoding(
                lot.name)

    def action_revaluation(self):
        self.ensure_one()
        view = self.env.ref(
            "stock_account.stock_valuation_layer_revaluation_form_view"
        )
        ctx = dict(
            self._context,
            default_lot_id=self.id,
            default_product_id=self.product_id.id,
            default_company_id=self.env.company.id,
        )
        return {
            "name": _("Lot/Serial Revaluation"),
            "view_mode": "form",
            "res_model": "stock.valuation.layer.revaluation",
            "view_id": view.id,
            "type": "ir.actions.act_window",
            "context": ctx,
            "target": "new",
        }
