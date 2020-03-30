# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression


class EngBomComp(models.Model):
    _name = 'engineering.bom.component'
    _description = 'Engineering BOM Import components'

    _sql_constraints = [(
        'part_unique',
        'unique (batch_id,filename,config_name)',
        "Part file/configuration must be unique per batch")]

    batch_id = fields.Many2one(
        comodel_name='engineering.bom.batch',
        required=True,
        readonly=True,
        ondelete='cascade')
    name = fields.Char(
        string='Part ID',
        help="Part number (e.g. X999999.Z9)")
    part_diff_id = fields.Many2one(
        comodel_name='engineering.part.diff',
        readonly=True,
        ondelete='set null')
    filename = fields.Char(
        string='filename')
    config_name = fields.Char(
        string='SW Config')
    part_num = fields.Char(
        string='Part Num')
    part_rev = fields.Char(
        string='Part Rev',
        default='-0')
    description = fields.Char(
        string='Part Name')
    material_spec = fields.Char(
        string='Material Spec')
    material_pn = fields.Char(
        string='Material PN')
    rm_qty = fields.Float(
        string='RM Qty')
    image = fields.Binary(
        string='Image',
        attachment=True,
        help="Image should be sized to 1024 x 1024px")
    part_type = fields.Char(
        string='Part Type')
    make = fields.Char(
        string='Make')
    coating = fields.Char(
        string='Coating Name')
    finish = fields.Char(
        string='Prep Name')
    uom = fields.Char(
        string='UOM Name')
    alt_qty = fields.Float(
        string='Alt Qty',
        default=0.0)
    route_template_name = fields.Char(
        string='Route Name')
    cutting_length_outer = fields.Float(
        string='Outer Cut Length')
    cutting_length_inner = fields.Float(
        string='Inner Cut Length')
    cut_out_count = fields.Integer(
        string='Cut-Outs')
    bend_count = fields.Integer(
        string='Bends')
    adjacency_parent_ids = fields.One2many(
        comodel_name='engineering.bom.adjacency',
        inverse_name='parent_comp_id')
    adjacency_child_ids = fields.One2many(
        comodel_name='engineering.bom.adjacency',
        inverse_name='child_comp_id')

    # matched fields
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        domain=['|', ('active', '=', True), ('active', '=', False)],
        ondelete='set null')
    product_active = fields.Boolean(
        related='product_id.active',
        string='Product Active',
        readonly=True)
    product_deprecated = fields.Boolean(
        related='product_id.deprecated',
        string='Obsolete',
        readonly=True)
    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='UOM')
    rm_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Raw Product',
        domain=['|', ('active', '=', True), ('active', '=', False)],
        ondelete='set null')
    route_template_id = fields.Many2one(
        comodel_name='mrp.routing',
        string='Route Id',
        ondelete='set null')
    suggested_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Suggested',
        ondelete='set null')
    eng_type_id = fields.Many2one(
        comodel_name='engineering.part.type',
        string='Eng Type')
    preparation_id = fields.Many2one(
        comodel_name='engineering.preparation',
        string='Prep')
    coating_id = fields.Many2one(
        comodel_name='engineering.coating',
        string='Coating')

    @api.model
    def set_product(self):
        prod_obj = self.env['product.product']
        routing_obj = self.env['mrp.routing']
        type_obj = self.env['engineering.part.type']
        coat_obj = self.env['engineering.coating']
        prep_obj = self.env['engineering.preparation']
        uom_obj = self.env['uom.uom']
        uom_name_map = {
            '': 'unit',
            'unit': 'unit',
            'inch': 'inch',
            'foot': 'foot',
            'sq-in': 'sq-in',
            'gal': 'gal',
            'qt': 'qt',
            'sq-ft': 'sq-ft',
            '1 only': 'unit',
            'e': 'unit',
            'ea': 'unit',
            'E': 'unit',
            'Ea': 'unit',
            'EA': 'unit',
            'fromparent+EA': 'unit',
            'in': 'inch',
            'IN': 'inch',
            'FT': 'foot',
            'ft.': 'foot',
            'Qts.': 'qt',
            'QT': 'qt',
            'gl': 'gal',
            'GL': 'gal',
            'SQ-FT': 'sq-ft',
            'SQ-IN': 'sq-in',
            'AR': 'unit',
            'CJE': 'unit',
        }
        coating_name_map = {
            '000A03': 'Paint, Gloss Black Industrial',
            '00A02': 'Powdercoat, Mouse Gray',
            '00A03': 'Paint, Gloss Black Industrial',
            '00A04': 'Paint, High Temp Silver/Aluminized',
            '00A05': 'Powdercoat, Carmine Red',
            '00B01': 'Powdercoat, Flat Black',
            '00B02': 'Powdercoat, Mouse Gray',
            '00C06': 'Powdercoat, Mouse Gray',
            '01A01': 'Powdercoat, Flat Black',
            '01A02': 'Powdercoat, Mouse Gray',
            '01A04': 'Paint, High Temp Silver/Aluminized',
            '01A05': 'Powdercoat, Carmine Red',
            '01B01': 'Powdercoat, Flat Black',
            '01C01': 'Powdercoat, Flat Black',
            '01C03': 'Paint, Gloss Black Industrial',
            '01C04': 'Paint, High Temp Silver/Aluminized',
            '01C05': 'Powdercoat, Carmine Red',
            '020B02': 'Powdercoat, Mouse Gray',
            '02A01': 'Powdercoat, Flat Black',
            '02A02': 'Powdercoat, Mouse Gray',
            '02A04': 'Paint, High Temp Silver/Aluminized',
            '02B01': 'Powdercoat, Flat Black',
            '02B02': 'Powdercoat, Mouse Gray',
            '02B03': 'Paint, Gloss Black Industrial',
            '02B04': 'Paint, High Temp Silver/Aluminized',
            '02B05': 'Powdercoat, Carmine Red',
            '02B06': 'Powdercoat, Mouse Gray',
            '02C01': 'Powdercoat, Flat Black',
            'Aluminized': 'Paint, High Temp Silver/Aluminized',
            'Anodize Clear': 'Anodize, Hard Clear',
            'BLACK': 'Powdercoat, Flat Black',
            'Black Anodize': 'Anodize, Hard Black',
            'Black Paint': 'Paint, Gloss Black Industrial',
            'Black Powder Coat': 'Powdercoat, Flat Black',
            'Black with Pinstripes': 'Powdercoat, Flat Black',
            'Black Zinc': 'Zinc Type II, Black',
            'BLACK ZINC': 'Zinc Type II, Black',
            'Black Zinc Oxide': 'Zinc Type II, Black',
            'Clear': 'Anodize, Hard Clear',
            'Flat Black Powder Coat': 'Powdercoat, Flat Black',
            'Gray': 'Powdercoat, Mouse Gray',
            'Gray Powder': 'Powdercoat, Mouse Gray',
            'Hard Black Anodized': 'Anodize, Hard Black',
            'Paint 01A04': 'Paint, High Temp Silver/Aluminized',
            'Paint 01C01': 'Powdercoat, Flat Black',
            'Paint 02A01': 'Powdercoat, Flat Black',
            'PAINT 02B01': 'Powdercoat, Flat Black',
            'Paint 02B01': 'Powdercoat, Flat Black',
            'PAINT 02B02': 'Powdercoat, Mouse Gray',
            'Paint 02B02': 'Powdercoat, Mouse Gray',
            'Paint 02B03': 'Paint, Gloss Black Industrial',
            'Paint Black': 'Paint, Gloss Black Industrial',
            'Painted Base': 'Paint, Gloss Black Industrial',
            'Powdercoat, Flat Black': 'Powdercoat, Flat Black',
            'Powdercoat, Mouse Gray': 'Powdercoat, Mouse Gray',
            'Powdered Red': 'Powdercoat, Carmine Red',
            'Yellow Powder Coat': 'Powdercoat, Safety Yellow',
            'Yellow Zinc': 'Zinc Type II, Yellow',
            'YELLOW ZINC': 'Zinc Type II, Yellow',
            'yellow zinc': 'Zinc Type II, Yellow',
            'Yellow Zinc Plated': 'Zinc Type II, Yellow',
            'Zinc': 'Zinc Type II, Yellow',
            'ZINC': 'Zinc Type II, Yellow',
            'Zinc Dichromate': 'Zinc Type II, Yellow',
            'Zinc Dichromate plate': 'Zinc Type II, Yellow',
            'Zinc Dichromate Plate': 'Zinc Type II, Yellow',
            'Zinc Dichromate Plated': 'Zinc Type II, Yellow',
            'Zinc Dichromate Plating': 'Zinc Type II, Yellow',
            'Zinc Dircromate': 'Zinc Type II, Yellow',
            'Zinc Plate': 'Zinc Type II, Yellow',
            'Zinc Plated': 'Zinc Type II, Yellow',
            'Zinc Plating': 'Zinc Type II, Yellow',
            'Zinc Type II Black': 'Zinc Type II, Black',
            'Powdercoat, Safety Yellow': 'Powdercoat, Safety Yellow',
            'Powdercoat, Carmine Red': 'Powdercoat, Carmine Red',
            'Paint, High Temp Silver/Aluminized': 'Paint, High Temp Silver/Aluminized',
            'Paint, High Temp Black': 'Paint, High Temp Black',
            'Zinc Type II, Yellow': 'Zinc Type II, Yellow',
            'Zinc Type II, Black': 'Zinc Type II, Black',
            'Paint, Gloss Black Industrial': 'Paint, Gloss Black Industrial',
            'Anodize, Hard Black': 'Anodize, Hard Black',
            'Anodize, Hard Clear': 'Anodize, Hard Clear',
            'Powdercoat, Gloss Black': 'Powdercoat, Gloss Black',
        }
        finish_name_map = {
            '02B02': 'Shot Blast',
            'BLAST': 'Shot Blast',
            'Machine': 'Machined',
            'Machined': 'Machined',
            'Mill Scale': 'Mill Scale',
            'Mill Scale Except Machined Areas': 'Mill Scale',
            'Millscale': 'Mill Scale',
            'Sand Blasted': 'Shot Blast',
            'Sandblast': 'Shot Blast',
            'Shot Blast': 'Shot Blast',
            'Turn-ground & polished': 'Turned, Ground, Polished',
            'Unpolished': 'Turned, Ground, Polished',
            'Wheel Abraided': 'Shot Blast',
        }
        for comp in self:
            comp.update({
                'product_id': False,
                'suggested_product_id': False,
                'rm_product_id': False,
                'route_template_id': False,
                'eng_type_id': False,
                'preparation_id': False,
                'coating_id': False,
                'uom_id': False,
            })
            comp.product_id = prod_obj.search(
                [('default_code', '=', comp.name),
                    '|', ('active', '=', True), ('active', '=', False)],
                limit=1)
            if not comp.product_id and comp.part_num:
                comp.suggested_product_id = prod_obj.search(
                    [('eng_code', '=', comp.part_num)],
                    order='default_code desc',
                    limit=1)
            comp.rm_product_id = comp.material_pn and prod_obj.search(
                [('default_code', '=', comp.material_pn)],
                limit=1)
            comp.route_template_id = comp.route_template_name and routing_obj.search(
                [('name', '=', comp.route_template_name)],
                limit=1)
            comp.eng_type_id = comp.part_type and type_obj.search(
                [('code', '=', comp.part_type)],
                limit=1)
            comp.preparation_id = comp.finish and prep_obj.search(
                [('name', '=', finish_name_map.get(comp.finish, comp.finish))],
                limit=1)
            comp.coating_id = comp.coating and coat_obj.search(
                [('name', '=', coating_name_map.get(comp.coating, comp.finish))],
                limit=1)
            comp.uom_id = uom_obj.search(
                [('name', '=', uom_name_map.get(comp.uom, comp.uom))],
                limit=1)
