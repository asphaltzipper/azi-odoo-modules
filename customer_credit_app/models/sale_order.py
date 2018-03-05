# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions


class SaleOrder(models.Model):
    _inherit = "sale.order"

    credit_app_date = fields.Date(
        related='partner_id.credit_app_date',
        readonly=True)
