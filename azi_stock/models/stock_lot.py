from odoo import models, fields, api, _


class ProductionLot(models.Model):
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
            lot.code128 = self.env['barcode.nomenclature'].get_code128_encoding(lot.name)
