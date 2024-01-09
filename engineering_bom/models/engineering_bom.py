# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class EngBom(models.Model):
    _name = 'engineering.bom'
    _description = 'Engineering BOM'

    _sql_constraints = [('part_bom_unique', 'unique (batch_id,name)', "Part BOM must be unique per batch")]

    batch_id = fields.Many2one(
        comodel_name='engineering.bom.batch',
        required=True,
        readonly=True,
        ondelete='cascade')
    name = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True)
    bom_id = fields.Many2one(
        comodel_name='mrp.bom',
        ondelete='set null')
    uom_id = fields.Many2one(
        related='bom_id.product_uom_id',
        string='UOM',
        readonly=True)
    quantity = fields.Float(
        string='Batch Qty',
        default=1.0)
    # TODO Routing
    # route_template_id = fields.Many2one(
    #     comodel_name='mrp.routing',
    #     string='Route Template')
    type = fields.Selection(
        selection=[
            ('normal', 'Normal'),
            ('phantom', 'Kit/Phantom')],
        string='BoM Type',
        default='normal',
        required=True,
        help="Kit/Phantom: Pickings will show the raw materials, instead of the finished product.")
    bom_line_ids = fields.One2many(
        comodel_name='engineering.bom.line',
        inverse_name='eng_bom_id')
    rm_part = fields.Boolean(
        string='Is RM Part',
        required=True,
        default=False)

    def set_bom(self):
        for eng_bom in self:
            eng_bom.bom_id = self.env['mrp.bom']._bom_find(
                product_tmpl=eng_bom.name.product_id.product_tmpl_id,
                product=eng_bom.name.product_id)


class EngBomLine(models.Model):
    _name = 'engineering.bom.line'
    _description = 'Engineering BOM Line'
    _order = 'eng_bom_id, name'

    _sql_constraints = [('component_unique', 'unique (eng_bom_id,name)', "Component must be unique per BOM")]

    eng_bom_id = fields.Many2one(
        comodel_name='engineering.bom',
        required=True,
        readonly=True,
        ondelete='cascade')
    name = fields.Many2one(
        comodel_name='product.product',
        string='Component',
        required=True,
        ondelete='cascade')
    uom_id = fields.Many2one(
        related='name.product_tmpl_id.uom_id',
        string='UOM',
        readonly=True)
    quantity = fields.Float(
        string='Qty',
        help="BOM quantity in the default stocking unit of measure for the product")
