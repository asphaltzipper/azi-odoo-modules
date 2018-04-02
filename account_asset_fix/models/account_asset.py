# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'

    @api.multi
    def _compute_entries(self, date, group_entries=False):
        depreciation_ids = self.env['account.asset.depreciation.line'].search([
            ('asset_id', 'in', self.ids), ('depreciation_date', '<=', date),
            ('move_check', '=', False)])
        if group_entries:
            post_move = self.env.context.get('post_move', True)
            return depreciation_ids.with_context(depreciation_date=date).create_grouped_move(post_move=post_move)
        return depreciation_ids.create_move()
