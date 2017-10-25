# -*- encoding: utf-8 -*-

from odoo import models


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    def _make_po_get_domain(self, partner):
        # don't add to purchase orders that are associated with a purchase
        # agreement, unless the purchase agreement is for this product
        import pdb
        pdb.set_trace()
        domain = super(ProcurementOrder, self)._make_po_get_domain(partner)
        req_domain = [('product_id', '=', self.product_id.id)]
        product_requisitions = self.env['purchase.requisition.line'].search(req_domain).mapped('requisition_id')
        domain += (
            '|',
            ('requisition_id', '=', False),
            ('requisition_id', 'in', tuple([x.id for x in product_requisitions]))
        )
        # domain += ((
        #     '|',
        #     ('requisition_id', '=', False),
        #     ('requisition_id', 'in', [x.id for x in product_requisitions])),)
        return domain
