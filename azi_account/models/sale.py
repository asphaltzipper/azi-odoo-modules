from odoo import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _finalize_invoices(self, invoices, references):
        super(SaleOrder, self)._finalize_invoices(invoices, references)
        for invoice in invoices.values():
            if self.filtered(lambda s: s.invoice_status == 'invoiced'):
                invoice._onchange_invoice_line_ids()
