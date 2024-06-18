from odoo import models, fields, api


class ProductMrpArea(models.Model):
    _name = 'product.mrp.area'
    _inherit = ['product.mrp.area', 'mail.thread']

    mrp_nbr_days = fields.Integer(
        tracking=True,
    )
    mrp_minimum_stock = fields.Integer(
        tracking=True,
    )
    mrp_minimum_order_qty = fields.Integer(
        tracking=True,
    )
    mrp_maximum_order_qty = fields.Integer(
        tracking=True,
    )
    mrp_qty_multiple = fields.Integer(
        tracking=True,
    )
