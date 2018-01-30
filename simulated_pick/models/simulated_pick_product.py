# -*- coding: utf-8 -*-
# (c) 2014 scosist
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
import odoo.addons.decimal_precision as dp


class SimulatedPickProduct(models.TransientModel):
    _name = 'simulated.pick.product'

    sim_prod_id = fields.Many2one(
        comodel_name='product.product',
        string='Simulated Product',
        required=True,
        ondelete="no action",
        index=True)

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        ondelete="no action",
        index=True)

    product_qty = fields.Float(
        string="Req'd Qty",
        digits=dp.get_precision('Product Unit of Measure'),
        required=True)

    on_hand_before = fields.Float(
        string='On-Hand Before',
        digits=dp.get_precision('Product Unit of Measure'),
        required=True)

    on_hand_after = fields.Float(
        string='On-Hand After',
        digits=dp.get_precision('Product Unit of Measure'),
        required=True)

    short = fields.Float(
        string='Short',
        digits=dp.get_precision('Product Unit of Measure'),
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

    default_supplier_id = fields.Many2one(
        comodel_name='res.partner',
        string='Supplier',
        compute='_compute_default_supplier',
        readonly=True,
        index=True,
        store=True)

    @api.depends('product_id')
    def _compute_default_supplier(self):
        for line in self:
            line.default_supplier_id = line.product_id.seller_ids and line.product_id.seller_ids[0].name or False

    @api.multi
    def action_material_analysis(self):
        self.ensure_one()
        return self.product_id.action_material_analysis()
