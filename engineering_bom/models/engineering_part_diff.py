# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class EngPartDiff(models.Model):
    _name = 'engineering.part.diff'
    _description = 'Engineering Part Diff'

    batch_id = fields.Many2one(
        comodel_name='engineering.bom.batch',
        required=True,
        readonly=True,
        ondelete='cascade')
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        ondelete='set null')
    product_tmpl_id = fields.Many2one(
        related='product_id.product_tmpl_id',
        string='Template')
    comp_ids = fields.One2many(
        comodel_name='engineering.bom.component',
        inverse_name='part_diff_id')
    important = fields.Boolean(
        string='Important',
        required=True,
        default=False)

    description = fields.Text(
        string='Old Name')
    image = fields.Binary(
        string='Old Image',
        attachment=True)
    eng_type_id = fields.Many2one(
        comodel_name='engineering.part.type',
        string='Old Eng Type')
    make = fields.Char(
        string='Old Make')
    preparation_id = fields.Many2one(
        comodel_name='engineering.preparation',
        string='Old Prep')
    coating_id = fields.Many2one(
        comodel_name='engineering.coating',
        string='Old Coating')
    uom_id = fields.Many2one(
        comodel_name='product.uom',
        string='Old UOM')
    cutting_length_outer = fields.Float(
        string='Old Outer Cut Length')
    cutting_length_inner = fields.Float(
        string='Old Inner Cut Length')
    cut_out_count = fields.Integer(
        string='Old Cutouts')
    bend_count = fields.Integer(
        string='Old Bends')

    description_new = fields.Char(
        string='New Name')
    image_new = fields.Binary(
        string='New Image',
        attachment=True)
    eng_type_new_id = fields.Many2one(
        comodel_name='engineering.part.type',
        string='New Type')
    make_new = fields.Char(
        string='New Make')
    preparation_new_id = fields.Many2one(
        comodel_name='engineering.preparation',
        string='New Prep')
    coating_new_id = fields.Many2one(
        comodel_name='engineering.coating',
        string='New Coating')
    uom_new_id = fields.Many2one(
        comodel_name='product.uom',
        string='New UOM')
    cutting_length_outer_new = fields.Float(
        string='New Outer Cut Length')
    cutting_length_inner_new = fields.Float(
        string='New Inner Cut Length')
    cut_out_count_new = fields.Integer(
        string='New Cut-Outs')
    bend_count_new = fields.Integer(
        string='New Bends')
