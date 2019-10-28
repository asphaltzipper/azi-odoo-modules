# -*- coding: utf-8 -*-

from odoo import models, fields, api


class EngineeringPartType(models.Model):
    _name = 'engineering.part.type'

    name = fields.Char(
        string="Type",
        required=True)
    code = fields.Char(
        string="Code",
        required=True)
    description = fields.Text(
        string="Description",
        required=True)
