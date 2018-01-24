# -*- coding: utf-8 -*-

from odoo import models, fields


class EngineeringPreparation(models.Model):
    _name = 'engineering.preparation'

    name = fields.Char()


class EngineeringCoating(models.Model):
    _name = 'engineering.coating'

    name = fields.Char()
