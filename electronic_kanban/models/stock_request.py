from odoo import api, models, fields, _


class StockRequest(models.AbstractModel):
    _inherit = 'stock.request.abstract'

    product_deprecated = fields.Boolean(
        related='product_id.deprecated',
        readonly=True,
        store=True)

    product_active = fields.Boolean(
        related='product_id.active',
        readonly=True,
        store=True)

    product_responsible_id = fields.Many2one(
        related='product_id.responsible_id',
        readonly=True,
        store=True)
