from odoo import api, fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    discount_reason_id = fields.Many2one(
        comodel_name='sale.discount.reason',
        string='Discount Reason',
        readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['discount_reason_id'] = ", l.discount_reason_id as discount_reason_id"
        groupby += ', l.discount_reason_id'
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
