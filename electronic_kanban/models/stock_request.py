from odoo import api, models, fields, _


class StockRequest(models.AbstractModel):
    _inherit = 'stock.request.abstract'

    product_deprecated = fields.Boolean(
        related='product_id.deprecated',
        string='Obsolete',
        readonly=True,
        store=True)

    product_active = fields.Boolean(
        related='product_id.active',
        string='Product Active',
        readonly=True,
        store=True)

    product_responsible_id = fields.Many2one(
        related='product_id.responsible_id',
        readonly=True,
        store=True)

    product_type = fields.Selection(
        related='product_id.type',
        readonly=True,
        store=True)
