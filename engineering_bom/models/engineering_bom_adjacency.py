# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class EngBomAdjacency(models.Model):
    _name = 'engineering.bom.adjacency'
    _description = 'Engineering BOM Component Adjacency'

    batch_id = fields.Many2one(
        comodel_name='engineering.bom.batch',
        required=True,
        readonly=True,
        ondelete='cascade')
    parent_comp_id = fields.Many2one(
        comodel_name='engineering.bom.component',
        ondelete='cascade',
        required=True)
    child_comp_id = fields.Many2one(
        comodel_name='engineering.bom.component',
        ondelete='cascade',
        required=True)
    count = fields.Integer(
        string='Count',
        required=True)
