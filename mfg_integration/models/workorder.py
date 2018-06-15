# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    priority_code = fields.Integer(
        string='Priority',
        compute='_compute_priority')

    def _compute_priority(self):
        """
        priority code must be between 2 and 10
        we want to scale 2 weeks worth of orders into the 2-10 range
        anything more than 2 weeks into the future gets a priority of 10
        """
        d0 = date.today()
        for rec in self:
            d1 = fields.Date.from_string(rec.production_date)
            diff_days = (d1 - d0).days
            if diff_days < 2:
                rec.priority_code = 2
            elif diff_days > 14:
                rec.priority_code = 10
            else:
                # the order is scheduled to complete between 3 and 14 days in the future
                # example 1:
                #     3/2+2=3.5
                #     int(3.5)=3
                # example 2:
                #     14/2+2=9
                #     int(9)=9
                rec.priority_code = int(diff_days / 2 + 2)
