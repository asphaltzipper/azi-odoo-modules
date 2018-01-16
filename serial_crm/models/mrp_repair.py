# -*- coding: utf-8 -*-

from odoo import fields, models


class Repair(models.Model):
    _inherit = 'mrp.repair'

    move_date = fields.Datetime(
        string="Move Date",
        related='move_id.date',
        readonly=True,
        store=True)
