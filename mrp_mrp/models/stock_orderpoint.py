# -*- coding: utf-8 -*-

from odoo import fields, models


class Orderpoint(models.Model):
    """ Defines Minimum stock rules. """
    _inherit = "stock.warehouse.orderpoint"

    no_batch = fields.Boolean(
        string='One Per Order',
        required=True,
        default=False,
        help="The MRP planning engine only will generate orders for quantity"
             " of 1.  This product will not be built in batches.")
