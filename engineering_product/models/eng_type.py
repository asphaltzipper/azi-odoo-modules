# -*- coding: utf-8 -*-

from odoo import models, fields, api


class EngineeringPartType(models.Model):
    _name = 'engineering.part.type'
    _description = "Engineering Part Type"
    _sql_constraints = [('engineering_part_type_code_unique', 'unique (code)', "Part type code must be unique")]

    name = fields.Char(
        string="Type",
        required=True)
    code = fields.Char(
        string="Code",
        required=True)
    description = fields.Text(
        string="Description",
        required=True)
