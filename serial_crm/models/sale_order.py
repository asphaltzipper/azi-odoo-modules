from odoo import models, fields, api, exceptions


class SaleOrder(models.Model):
    _inherit = "sale.order"

    related_lot_ids = fields.Many2many(
        comodel_name='stock.lot',
        relation='related_sale_order_stock_lot_rel',
        column1='sale_order_id',
        column2='stock_lot_id',
        string="Related Serials",
    )
