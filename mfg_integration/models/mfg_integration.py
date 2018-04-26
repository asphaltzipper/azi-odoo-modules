# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # Manufacturing
    rm_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Raw Material')
    raw_material_qty = fields.Float(
        string='Raw Material Qty')
    rm_material_code = fields.Char(
        readonly=True,
        string='Material Code',
        compute='_compute_material')
    rm_gauge_code = fields.Char(
        readonly=True,
        string='Thickness Code',
        compute='_compute_gauge')
    formed = fields.Boolean(
        string='Formed')
    mfg_code = fields.Char(
        string='File',
        compute='_compute_mfg_code')
    mfg_routing = fields.Many2one(
        comodel_name='mrp.routing',
        string='Routing')

    # Raw Material Attributes
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
    laser_thickness = fields.Char(
        readonly=True,
        string='Laser Thickness',
        compute='_compute_laser_gauge')

    def _compute_mfg_code(self):
        for rec in self:
            rec.mfg_code = rec.eng_code + rec.eng_rev

    def _compute_gauge(self):
        for rec in self:
            rec.rm_gauge_code = rec.rm_product_id.gauge_id.name

    def _compute_material(self):
        for rec in self:
            rec.rm_material_code = rec.rm_product_id.material_id.name

    def _compute_laser_gauge(self):
        for rec in self:
            rec.laser_thickness = rec.rm_product_id.gauge_id.laser_gauge

    @api.onchange('material_id')
    def onchange_material_id(self):
        if self.material_id:
            self.gauge_id = False

    def button_create_bom(self):
        self.ensure_one()
        # get mrp.bom object
        bom = self.env['mrp.bom']
        # check for existing bom
        if bom.search([('product_tmpl_id', '=', self.id)]):
            raise UserError(_('BOM already Exists'))

        # build dictionary of bom values
        res = {
            'product_id': self.product_variant_ids[0].id,
            'type': 'normal',
            'product_tmpl_id': self.id,
            'code': self.default_code,
            'product_qty': '1',
            'product_uom_id': self.uom_id.id
        }
        bom_id = bom.create(res)

        #  build dict of bom line values
        bom_line = self.env['mrp.bom.line']
        # build dictionary of bom line values
        res = {
            'bom_id': bom_id.id,
            'product_id': self.rm_product_id.id,
            'product_qty': self.raw_material_qty,
            'product_uom_id': self.rm_product_id.uom_id.id
        }
        bom_line.create(res)

        # add routing
        if bom_id.product_tmpl_id.formed:
            route = self.env.ref('mfg_integration.routing_laser_break_template')
        else:
            route = self.env.ref('mfg_integration.routing_laser_template')
        if not route:
            raise UserError(_('No routing found'))
        new_route = route.copy()
        new_route.name = bom_id.product_tmpl_id.eng_code
        bom_id.routing_id = new_route.id

    _sql_constraints = [
        ('common_cutting_qty_check', "CHECK ( common_cutting_qty > 1 )", "The number of common cuts must be greater than 1."),
    ]


class MfgGauge(models.Model):
    _name = 'mfg.gauge'

    name = fields.Char(
        string='Typical Thickness'
    )

    laser_gauge = fields.Char(
        string='Laser Thickness'
    )

    material_id = fields.Many2one(
        comodel_name='mfg.material',
        string='Raw Material')

    _sql_constraints = [
        ('raw_material_thickness_check', "CHECK ( common_cutting_qty > 1 )", "The number of common cuts must be greater than 1."),
    ]


class MfgMaterial(models.Model):
    _name = 'mfg.material'

    name = fields.Char()
