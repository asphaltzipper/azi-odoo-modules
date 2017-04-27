# -*- coding: utf-8 -*-
# (c) 2014 scosist
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class SimulatedPickProduct(models.TransientModel):
    _name = 'simulated.pick.product'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        ondelete="no action",
        select=True)

    product_qty = fields.Float(
        string="Req'd Qty",
        digits_compute=dp.get_precision('Product Unit of Measure'),
        required=True)

    on_hand_before = fields.Float(
        string='On-Hand Before',
        digits_compute=dp.get_precision('Product Unit of Measure'),
        required=True)

    on_hand_after = fields.Float(
        string='On-Hand After',
        digits_compute=dp.get_precision('Product Unit of Measure'),
        required=True)

    short = fields.Float(
        string='Short',
        digits_compute=dp.get_precision('Product Unit of Measure'),
        required=True)

    proc_action = fields.Char(string='Action')

    categ_id = fields.Many2one(
        comodel_name='product.category',
        related='product_id.categ_id',
        string='Internal Category',
        store=True)

    product_uom = fields.Many2one(
        comodel_name='product.uom',
        related='product_id.uom_id',
        string='UoM',
        store=True)
