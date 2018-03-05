# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    credit_app_date = fields.Date(
        string='Credit App Date')
