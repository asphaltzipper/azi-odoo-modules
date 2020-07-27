# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ChangeStockRequest(models.TransientModel):
    _name = 'change.stock.request'

    expected_date = fields.Datetime('Expected Date')

    @api.multi
    def change_date_of_request(self):
        requests = self.env['stock.request'].search([('id', 'in', self._context['active_ids']),
                                                     ('state', 'not in', ('done', 'cancel')), ('scheduled', '=', True)])
        for request in requests:
            request.expected_date = self.expected_date
            order = self.env['mrp.production'].search([('origin', '=', request.name)])
            if order:
                order.date_planned_finished = self.expected_date

