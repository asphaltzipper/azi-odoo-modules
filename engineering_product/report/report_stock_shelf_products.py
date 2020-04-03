# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class ReportStockShelfProducts(models.Model):
    _inherit = 'report.stock.shelf.products'

    deprecated = fields.Boolean(
        string='Deprecated',
        required=True)

    def _select_fields(self):
        select_fields = super(ReportStockShelfProducts, self)._select_fields()
        select_fields.append('deprecated')
        return select_fields

    def _sub_select_fields(self):
        select_fields = super(ReportStockShelfProducts, self)._sub_select_fields()
        select_fields.append('t.deprecated')
        return select_fields

    def _template_aggregate_fields(self):
        select_fields = super(ReportStockShelfProducts, self)._template_aggregate_fields()
        select_fields.append('bool_and(p.deprecated) as deprecated')
        return select_fields
