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
        store=True,
        readonly=True)
    routing_detail = fields.Char(
        string="Routing Detail",
        compute='_compute_mfg_properties')
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
                   ('4', 'any orientation'),
                   ('5', '0° or 180°'),
                   ('6', '90° or 270°'),
                   ('7', '0°, 90°, 180° or 270°')],
        string='Orientation',
        default='4')
    laser_code = fields.Char(
        readonly=True,
        string='Laser Thickness Code',
        compute='_compute_mfg_properties')
    has_etching = fields.Boolean(
        string="Etch",
        default=False,
        required=True,
        help="This part has laser etching")

    @api.depends('categ_id', 'product_variant_ids', 'product_variant_ids.default_code')
    def _compute_mfg_code(self):
        unique_variants = self.filtered(lambda t: len(t.product_variant_ids) == 1 and t.categ_id.eng_management)
        for template in unique_variants:
            eng_code, eng_rev = template.product_variant_ids._parse_default_code(
                template.product_variant_ids.default_code,
                template.categ_id.def_code_regex
            )
            template.mfg_code = eng_code and eng_code + eng_rev or False

    @api.depends('bom_ids')
    def _compute_mfg_properties(self):
        for rec in self:
            bom = rec.bom_ids and rec.bom_ids[0] or False
            if rec.bom_ids and rec.bom_ids[0].one_comp_product_id:
                rec.rm_product_id = bom.one_comp_product_id
                rec.raw_material_qty = bom.one_comp_product_qty
                # rec.raw_material_uom_id = bom.one_comp_product_uom_id
                rec.rm_material_code = bom.one_comp_product_id.material_id.name
                rec.rm_gauge_code = bom.one_comp_product_id.gauge_id.name
                rec.laser_code = bom.one_comp_product_id.gauge_id.laser_code
                rec.routing_detail = ", ".join([x for x in bom.operation_ids.mapped('workcenter_id.code') if x])
            else:
                rec.rm_product_id = None
                rec.raw_material_qty = 0
                rec.rm_material_code = None
                rec.rm_gauge_code = None
                rec.laser_code = None

    @api.depends('bend_count')
    def _compute_formed(self):
        for rec in self:
            rec.formed = bool(rec.bend_count)

    _sql_constraints = [
        ('common_cutting_qty_check',
         "CHECK ( common_cutting_qty > 1 )",
         "The number of common cuts must be greater than 1."),
    ]

    @api.onchange('material_id')
    def onchange_material_id(self):
        """
        Clear the gauge field when the material field is changed
        """
        self.update({
            'gauge_id': False,
        })
        if not self.material_id:
            return {'domain': {'gauge_id': [('id', 'in', [])]}}
        return {'domain': {'gauge_id': [('id', 'in', self.material_id.gauge_ids.ids)]}}
