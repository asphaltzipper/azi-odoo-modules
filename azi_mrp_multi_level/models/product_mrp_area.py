from odoo import models, fields, api


class ProductMrpArea(models.Model):
    _name = 'product.mrp.area'
    _inherit = ['product.mrp.area', 'mail.thread']

    mrp_nbr_days = fields.Integer(
        track_visibility='onchange',
    )
    mrp_minimum_stock = fields.Integer(
        track_visibility='onchange',
    )
    mrp_minimum_order_qty = fields.Integer(
        track_visibility='onchange',
    )
    mrp_maximum_order_qty = fields.Integer(
        track_visibility='onchange',
    )
    mrp_qty_multiple = fields.Integer(
        track_visibility='onchange',
    )
