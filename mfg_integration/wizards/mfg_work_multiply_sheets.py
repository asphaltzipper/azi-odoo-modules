# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class MfgWorkMultiSheets(models.TransientModel):
    _name = 'mfg.work.multiply.sheets'
    _description = 'Multiply mfg work by number of sheets'

    sheet_count = fields.Integer(
        string="Num Sheets")

    header_id = fields.Many2one(
        comodel_name='mfg.work.header',
        string="MFG Work Import Header",
        readonly=True,
        required=True,
        ondelete='cascade')

    @api.model
    def default_get(self, fields):
        res = super(MfgWorkMultiSheets, self).default_get(fields)
        res['header_id'] = self._context['active_id']
        header = self.env['mfg.work.header'].browse(res['header_id'])
        res['sheet_count'] = header.number_sheets or 1
        return res

    @api.multi
    def action_multiply(self):
        """Multiply quantity produced by the number of sheets."""
        self.header_id.change_sheets(self.sheet_count)
        return {}
