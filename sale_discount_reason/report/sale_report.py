# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    discount_reason_id = fields.Many2one(
        comodel_name='sale.discount.reason',
        string='Discount Reason')

    def _select(self):
        select_str = super(SaleReport, self)._select()
        select_str += ', l.discount_reason_id'
        return select_str

    def _group_by(self):
        group_by_str = super(SaleReport, self)._group_by()
        group_by_str += ', l.discount_reason_id'
        return group_by_str
