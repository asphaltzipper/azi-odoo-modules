import datetime
from odoo import models, api


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.model
    def _prepare_purchase_order_line_from_procurement(self, product_id, product_qty, product_uom, company_id, values,
                                                      po):
        res = super(PurchaseOrderLine, self)._prepare_purchase_order_line_from_procurement(
            product_id, product_qty, product_uom, company_id, values,po)
        if self.env.context.get('active_model', False) == 'stock.request':
            stock_request_id = self.env.context.get('stock_request_id', False)
            if stock_request_id:
                stock_request = self.env['stock.request'].browse(stock_request_id)
                res.update(date_planned=datetime.datetime.now() + datetime.timedelta(days=stock_request.product_id.produce_delay))
        return res
