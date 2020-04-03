# -*- coding:utf-8 -*-

from odoo import api, models


class ReportCountSheets(models.AbstractModel):
    _name = 'report.shelf_location.shelf_count_sheets'
    _description = 'Shelf Count Sheets'

    @api.model
    def _get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('shelf_location.shelf_count_sheets')
        group_docs = self.env['report.stock.shelf.products'].browse(docids).group_shelf_products()
        loc_count = len(group_docs)
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': group_docs,
            'loc_count': loc_count,
        }
        return docargs
