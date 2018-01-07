# -*- coding:utf-8 -*-

from odoo import api, models


class ReportCountSheets(models.AbstractModel):
    _name = 'report.shelf_location.shelf_count_sheets'

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('shelf_location.shelf_count_sheets')
        group_docs = self.env['stock.shelf.products'].browse(docids).group_shelf_products()
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': group_docs,
        }
        return report_obj.render('shelf_location.shelf_count_sheets', docargs)
