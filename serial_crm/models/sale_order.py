from odoo import models, fields, api, exceptions


class SaleOrder(models.Model):
    _inherit = "sale.order"

    lot_ids = fields.Many2many(
        comodel_name='stock.production.lot',
        string="Related Serials")
