# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    one_comp_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Component',
        compute='_compute_one_component',
        help="The one and only component, if a single product line on this BOM.")

    one_comp_product_qty = fields.Float(
        string='Comp Qty',
        compute='_compute_one_component')

    one_comp_product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Comp UOM',
        compute='_compute_one_component')

    routing_name = fields.Char(
        compute='_compute_routing_name',
        string='Routing Name',
        store=True,
    )

    deprecated = fields.Boolean(
        string="Obsolete",
        related='product_tmpl_id.deprecated')

    def _compute_one_component(self):
        for bom in self:
            if len(bom.bom_line_ids) == 1:
                bom.one_comp_product_id = bom.bom_line_ids[0].product_id
                bom.one_comp_product_qty = bom.bom_line_ids[0].product_qty
                bom.one_comp_product_uom_id = bom.bom_line_ids[0].product_uom_id
            else:
                bom.one_comp_product_id = None
                bom.one_comp_product_qty = 0
                bom.one_comp_product_uom_id = None

    @api.depends('operation_ids')
    def _compute_routing_name(self):
        for bom in self:
            wc_codes = bom.operation_ids.mapped('workcenter_id.code')
            bom.routing_name = any(wc_codes) and ", ".join(wc_codes)
