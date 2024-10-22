# Copyright 2024 Matt Taylor
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_is_zero
from odoo.tools.misc import groupby


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.depends(
        'company_id',
        'location_id',
        'owner_id',
        'product_id',
        'lot_id',
        'quantity',
    )
    def _compute_value(self):
        untracked = self.filtered(
            lambda x: x.product_id.categ_id.property_cost_method != 'fifo'
                      or x.product_id.tracking == 'none'
                      or not x.lot_id
        )
        super(StockQuant, untracked)._compute_value()
        tracked = self - untracked
        for quant in tracked:
            quant.currency_id = quant.company_id.currency_id
            rounding = quant.product_id.uom_id.rounding
            if (
                not quant.location_id
                or not quant.product_id
                or not quant.location_id._should_be_valued()
                or quant._should_exclude_for_valuation()
                or float_is_zero(quant.quantity, precision_rounding=rounding)
            ):
                quant.value = 0
                continue
            unit_value = quant.lot_id.with_company(quant.company_id).unit_value_svl
            quant.value = quant.quantity * unit_value
