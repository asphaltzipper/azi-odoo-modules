from odoo import api, fields, models


class StockRequestKanban(models.Model):
    _inherit = "stock.request.kanban"

    code128 = fields.Char(
        string="Code128 Encoded Name",
        compute="_compute_code128",
        store=True,
    )

    @api.depends('name')
    def _compute_code128(self):
        for kanban in self:
            if not kanban.name:
                kanban.code128 = False
                continue
            kanban.code128 = self.env['barcode.nomenclature'].get_code128_encoding(kanban.name)
