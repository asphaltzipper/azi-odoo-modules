# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class EngBomDiff(models.Model):
    _name = 'engineering.bom.diff'
    _description = 'Engineering BOM Diff'

    batch_id = fields.Many2one(
        comodel_name='engineering.bom.batch',
        required=True,
        readonly=True,
        ondelete='cascade')
    bom_id = fields.Many2one(
        comodel_name='mrp.bom',
        string="MRP BOM",
        readonly=True,
        ondelete='set null')
    eng_bom_id = fields.Many2one(
        comodel_name='engineering.bom',
        string="Eng BOM",
        ondelete='cascade',
        readonly=True)
    rm_part = fields.Boolean(
        string='Is RM Part',
        required=True,
        default=False)
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        ondelete='set null')
    action_type = fields.Selection(
        selection=[
            ('add', '+ + +'),
            ('remove', '- - -'),
            ('change', '~ ~ ~'),
        ],
        string='Action',
        readonly=True,
        required=True,
        help="+ + + Add\n- - - Remove\n~ ~ ~ Change")

    # old values
    qty = fields.Float(
        string='Old Qty',
        required=True,
        readonly=True,
        default=1.0)
    route_template_id = fields.Many2one(
        comodel_name='mrp.routing',
        ondelete='set null',
        readonly=True,
        string='Old Route Name')
    route_detail = fields.Char(
        related='route_template_id.operations_detail',
        string='Old Route',
        store=True)
    type = fields.Selection(
        selection=[
            ('normal', 'Normal'),
            ('phantom', 'Kit/Phantom')],
        string='Old Type')

    # new values
    qty_new = fields.Float(
        string='New Qty',
        readonly=True,
        required=True,
        default=1.0,
        help="Production batch quantity in new BOM")
    route_template_new_id = fields.Many2one(
        comodel_name='mrp.routing',
        ondelete='set null',
        string='New Route Name')
    route_detail_new = fields.Char(
        related='route_template_new_id.operations_detail',
        string='New Route',
        store=True)
    type_new = fields.Selection(
        selection=[
            ('normal', 'Normal'),
            ('phantom', 'Kit/Phantom')],
        string='New Type')

    # this is not necessary because we will be accessing old and new values to
    # check whether we even need to create a diff record
    # def create(self, values):
    #     if values.get('bom_id'):
    #         bom_obj = self.env['mrp.bom']
    #         bom = bom_obj.search([('id', '=', values['bom_id'])])
    #         values['qty'] = bom.product_qty
    #         values['route_template_id'] = bom.routing_id
    #         values['type'] = bom.type
    #         values['action_type'] = 'change'
    #     else:
    #         values['action_type'] = 'new'
    #     super(EngBomDiff, self).create(values)


class EngBomLineDiff(models.Model):
    _name = 'engineering.bom.line.diff'
    _description = 'Engineering BOM Line Diff'
    _order = 'parent_id, action_type, name'

    batch_id = fields.Many2one(
        comodel_name='engineering.bom.batch',
        required=True,
        readonly=True,
        ondelete='cascade')
    eng_bom_id = fields.Many2one(
        # comodel_name='engineering.bom',
        related='eng_bom_line_id.eng_bom_id',
        string='Eng BOM',
        readonly=True,
        ondelete='cascade')
    rm_part = fields.Boolean(
        string='Is RM Part',
        required=True,
        default=False)
    eng_bom_line_id = fields.Many2one(
        comodel_name='engineering.bom.line',
        readonly=True,
        ondelete='cascade')
    mrp_bom_line_id = fields.Many2one(
        comodel_name='mrp.bom.line',
        ondelete='set null',
        readonly=True)
    mrp_bom_id = fields.Many2one(
        related='mrp_bom_line_id.bom_id',
        string='MRP BOM',
        readonly=True)
    parent_id = fields.Many2one(
        comodel_name='product.product',
        string='Parent',
        readonly=True,
        store=True,
        required=True)
    name = fields.Many2one(
        comodel_name='product.product',
        string='Component',
        ondelete='set null',
        readonly=True,
        required=True)
    qty = fields.Float(
        string='Old Qty',
        readonly=True,
        required=True,
        default=0.0,
        help="Component quantity in existing BOM")
    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Old UOM',
        ondelete='set null',
        readonly=True)
    qty_new = fields.Float(
        string='New Qty',
        readonly=True,
        required=True,
        help="Component quantity in new BOM")
    uom_new_id = fields.Many2one(
        comodel_name='uom.uom',
        string='New UOM',
        ondelete='set null',
        readonly=True)
    action_type = fields.Selection(
        selection=[
            ('add', '+ + +'),
            ('remove', '- - -'),
            ('change', '~ ~ ~'),
            ('option', '- o -'),
        ],
        string='Action',
        readonly=True,
        required=True,
        help="+ + + Add\n- - - Remove\n~ ~ ~ Change\n- o - Option")
    state = fields.Selection(
        related='batch_id.state',
        readonly=True)
