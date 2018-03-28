# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"
    transport_note = fields.Text(string='Transport Note', translate=True)
