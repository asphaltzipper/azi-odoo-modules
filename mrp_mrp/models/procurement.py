# -*- encoding: utf-8 -*-

from odoo import models, fields
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    def _make_po_get_domain(self, partner):
        # don't add to purchase orders that are associated with a purchase
        # agreement, unless the purchase agreement is for this product
        domain = super(ProcurementOrder, self)._make_po_get_domain(partner)
        req_domain = [('product_id', '=', self.product_id.id)]
        product_requisitions = self.env['purchase.requisition.line'].search(req_domain).mapped('requisition_id')
        domain += (
            '|',
            ('requisition_id', '=', False),
            ('requisition_id', 'in', tuple([x.id for x in product_requisitions]))
        )
        return domain

    def _get_purchase_order_date(self, schedule_date):
        order_date = super(ProcurementOrder, self)._get_purchase_order_date(schedule_date)
        now = datetime.strptime(fields.Datetime.now(), DEFAULT_SERVER_DATETIME_FORMAT)
        if order_date < now:
            return now
        return order_date
