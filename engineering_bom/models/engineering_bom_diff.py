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
    routing_name = fields.Char(
        string='Old Route Name',
        readonly=True,
    )
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
    routing_name_new = fields.Char(
        string='New Route Name',
        readonly=True,
    )
    type_new = fields.Selection(
        selection=[
            ('normal', 'Normal'),
            ('phantom', 'Kit/Phantom')],
        string='New Type')


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
        ondelete='cascade',
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
        help="+ + + Add\n- - - Remove\n~ ~ ~ Change Qty\n- o - Option Break")
    state = fields.Selection(
        related='batch_id.state',
        readonly=True)
