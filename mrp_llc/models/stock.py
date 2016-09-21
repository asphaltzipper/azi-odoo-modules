# -*- coding: utf-8 -*-
# See __openerp__.py file for full copyright and licensing details.

from odoo import fields, models


class stock_warehouse_orderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    llc = fields.Integer(string='Low Level Code', default=0, readonly=True)
