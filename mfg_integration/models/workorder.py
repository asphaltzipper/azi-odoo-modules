# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    priority_code = fields.Integer(
        string='Priority',
        compute='_compute_priority')

    def _compute_priority(self):
        d0 = date.today()
        for rec in self:
            d1 = fields.Date.from_string(rec.production_date)
            diff_days = d0 - d1
            code = diff_days.days / 2 + 2
            if code < 2:
                rec.priority_code = 2
            elif code > 10:
                rec.priority_code = 10
            else:
                rec.priority_code = code
