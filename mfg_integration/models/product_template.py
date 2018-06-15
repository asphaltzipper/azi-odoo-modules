# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # Manufacturing Summary Data
    rm_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Raw Material',
        compute='_compute_mfg_properties',
        readonly=True)
    raw_material_qty = fields.Float(
        string='Raw Material Qty',
        compute='_compute_mfg_properties',
        readonly=True)
    rm_material_code = fields.Char(
        string='Material Code',
        compute='_compute_mfg_properties',
        readonly=True)
    rm_gauge_code = fields.Char(
        string='Thickness Code',
        compute='_compute_mfg_properties',
        readonly=True)
    mfg_code = fields.Char(
        string='Mfg Code',
        compute='_compute_mfg_code',
        readonly=True)
    mfg_routing_id = fields.Many2one(
        comodel_name='mrp.routing',
        string='Routing',
        compute='_compute_mfg_properties',
        readonly=True)
    # only here for backward compatibility
    # TODO: remove this field
    formed = fields.Boolean(
        string="Formed",
        compute='_compute_formed',
        readonly=True)

    # Sheet Metal Manufacturing Attributes
    cutting_length_outer = fields.Float(
        string='Outer Cut Length')
    cutting_length_inner = fields.Float(
        string='Inner Cut Length')
    cut_out_count = fields.Integer(
        string='Cut-Outs')
    bend_count = fields.Integer(
        string='Bends')

    # Sheet Metal Raw Material Attributes
    is_continuous = fields.Boolean(
        string="Continuous",
        related='uom_id.category_id.is_continuous',
        readonly=True)
    material_id = fields.Many2one(
        comodel_name='mfg.material',
        string='Material')
    gauge_id = fields.Many2one(
        comodel_name='mfg.gauge',
        string='Thickness')

    # Laser Parts Info
    common_cutting = fields.Selection(
        selection=[('none', 'None'),
                   ('unrestricted', 'Unrestricted'),
                   ('same_part', 'Same Part')],
        default='none',
        string='Common Cutting')
    common_cutting_qty = fields.Integer(
        string='Common Cutting QTY',
        default=2)
    orientation = fields.Selection(
        selection=[('1', '0° only'),
                   ('2', '90° only'),
                   ('3', '0° or 90°'),
                   ('4', '0° or 180°'),
                   ('5', '90° or 270°'),
                   ('6', '0°, 90°, 180° or 270°'),
                   ('6', 'any orientation')],
        string='Orientation')
    laser_code = fields.Char(
        readonly=True,
        string='Laser Thickness Code',
        compute='_compute_mfg_properties')

    # @api.depends('product_variant_ids', 'product_variant_ids.eng_code', 'product_variant_ids.eng_rev')
    def _compute_mfg_code(self):
            unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
            for template in unique_variants:
                template.mfg_code = template.product_variant_ids.eng_code + template.product_variant_ids.eng_rev
            for template in (self - unique_variants):
                template.mfg_code = ''

    @api.depends('bom_ids')
    def _compute_mfg_properties(self):
        for rec in self:
            if rec.bom_ids and rec.bom_ids[0].one_comp_product_id:
                bom = rec.bom_ids[0]
                rec.rm_product_id = bom.one_comp_product_id
                rec.mfg_routing_id = bom.routing_id
                rec.raw_material_qty = bom.one_comp_product_qty
                rec.raw_material_uom_id = bom.one_comp_product_uom_id
                rec.rm_material_code = bom.one_comp_product_id.material_id.name
                rec.rm_gauge_code = bom.one_comp_product_id.gauge_id.name
                rec.laser_code = bom.one_comp_product_id.gauge_id.laser_code

    @api.depends('bend_count')
    def _compute_formed(self):
        for rec in self:
            rec.formed = bool(rec.bend_count)

    _sql_constraints = [
        ('common_cutting_qty_check',
         "CHECK ( common_cutting_qty > 1 )",
         "The number of common cuts must be greater than 1."),
    ]
