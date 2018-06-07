# -*- coding: utf-8 -*-

from datetime import date
from odoo import api, fields, models


class TaxReportWizard(models.TransientModel):

    _name = 'tax.report.wizard'

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        string='Company'
    )
    date_start = fields.Date(
        required=True)
    date_end = fields.Date(
        required=True)

    @api.multi
    def button_export_pdf(self):
        self.ensure_one()
        return self._export()

    def _prepare_tax_statement(self):
        self.ensure_one()
        return {
            'date_start': self.date_start,
            'date_end': self.date_end,
            'company_id': self.company_id.id,
            'partner_ids': self._context['active_ids'],
        }

    def _export(self):
        """Export to PDF."""
        data = self._prepare_outstanding_statement()
        return self.env['report'].with_context(landscape=False).get_action(
            self, 'sales_tax_reporting.account_tax_report', data=data)

    # def _export(self):
    #     """Export to PDF."""
    #     data = self._prepare_outstanding_statement()
    #     return self.env['report'].with_context(landscape=False).get_action(
    #         self, 'azi_account.tax_report', data=data)
