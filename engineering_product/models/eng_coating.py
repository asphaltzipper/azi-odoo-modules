# -*- coding: utf-8 -*-

from odoo import models, fields


class EngineeringPreparation(models.Model):
    _name = 'engineering.preparation'
    _sql_constraints = [('name_uniq', 'unique (name)', "Preparation already exists")]

    name = fields.Char(
        string='Name',
        required=True)


class EngineeringCoating(models.Model):
    _name = 'engineering.coating'
    _sql_constraints = [('name_uniq', 'unique (name)', "Coating already exists")]

    name = fields.Char(
        string='Name',
        required=True)
