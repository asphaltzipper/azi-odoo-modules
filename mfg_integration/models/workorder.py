# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import math


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    priority_code = fields.Integer(
        string='Priority',
        compute='_compute_priority')

    def _compute_priority(self):
        """
        Priority code must be between 2 and 9. That means we have 8 possible
        values. We assign each order a priority code based on the day it is
        scheduled to start.  Earlier orders get lower priority code, and later
        orders get higher priority code.  For example:
           - number of days spanned by selected orders = 21
           - factor = 8.0/21 = 0.38
           - order scheduled on day 1
             - priority = ceiling(0.38*1)+1 = 2
           - order scheduled on day 10
             - priority = ceiling(0.38*10)+1 = 5
           - order scheduled on day 21
             - priority = ceiling(0.38*1)+1 = 9
        """
        d_now = fields.Datetime.now()
        d_max = max(self.mapped('production_date'))
        span_days = (d_max - d_now).days
        factor = 8.0 / span_days
        for rec in self:
            day = (rec.production_date - d_now).days
            priority = int(math.ceil(day*factor)+1)
            rec.priority_code = min(max(priority, 2), 9)
