# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ChangeStockRequest(models.TransientModel):
    _name = 'change.stock.request'
    _description = "Change Stock Request"

    expected_date = fields.Datetime('Expected Date')

    @api.multi
    def change_date_of_request(self):
        requests = self.env['stock.request'].search([('id', 'in', self._context['active_ids']),
                                                     ('state', 'not in', ('done', 'cancel')), ('scheduled', '=', True)])
        for request in requests:
            request.expected_date = self.expected_date
            # update manufacturing order dates
            order = self.env['mrp.production'].search([
                ('origin', '=', request.name),
                ('state', 'not in', ('done', 'cancel')),
            ], limit=1)
            if order:
                order.date_planned_finished = self.expected_date
            # update sale order dates
            if request.sale_order_line_id:
                request.sale_order_line_id.order_id.commitment_date = self.expected_date
                pickings = request.sale_order_line_id.order_id.picking_ids
                for pick in pickings.filtered(lambda x: x.state not in ['done', 'cancel']):
                    pick.scheduled_date = self.expected_date
