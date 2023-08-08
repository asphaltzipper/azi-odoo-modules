from odoo import api, fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    discount_reason_id = fields.Many2one(
        comodel_name='sale.discount.reason',
        string='Discount Reason',
        readonly=True)

    def _select_additional_fields(self):
        res = super(SaleReport, self)._select_additional_fields()
        res['discount_reason_id'] = "l.discount_reason_id"
        return res

    def _group_by_sale(self):
        res = super(SaleReport, self)._group_by_sale()
        res += ', l.discount_reason_id'
        return res
