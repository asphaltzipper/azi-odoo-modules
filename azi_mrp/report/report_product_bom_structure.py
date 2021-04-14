# -*- coding: utf-8 -*-

import json

from odoo import api, models, _
from odoo.tools import float_round


class ReportProductBom(models.AbstractModel):
    _name = 'report.azi_mrp.report_product_bom'
    _description = 'Product BOM Structure'

    @api.model
    def get_html(self, product_id=False):
        res = self._get_report_data(product_id)
        res['lines'] = self.env.ref('azi_mrp.report_product_bom').render({'data': res['lines']})
        return res

    def _get_bom_reference(self, bom):
        return bom.display_name

    @api.model
    def _get_report_data(self, product_id):
        product = self.env['product.product'].browse(product_id)
        bom_lines = self.env['mrp.bom.line'].search([('product_id', '=', product.id)])
        lines = self._get_bom(bom_lines)
        return {
            'lines': lines,
        }

    def _get_bom(self, bom_line_ids=False):
        lines = []
        for line in bom_line_ids:
            lines.append({
                'product': line.product_id,
                'product_template': line.product_id.product_tmpl_id,
                'bom_id': line.bom_id,
                'bom_line_id': line.id,
                'quantity': line.product_qty,
                'uom': line.product_uom_id,
                'type': line.bom_id.type,
                'active': line.product_id.active,
                'deprecated': line.product_id.deprecated,
            })
        return lines
