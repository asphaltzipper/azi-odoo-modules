# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    @api.depends('name', 'state', 'date')
    def name_get(self):
        result = []
        for move in self:
            if move._context.get('purchase_view', False):
                name = move.date
            elif move.state == 'draft':
                name = '* ' + str(move.id)
            else:
                name = move.name
            result.append((move.id, name))
        return result
