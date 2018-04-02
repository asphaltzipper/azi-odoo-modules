# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class AssetDepreciationConfirmationWizard(models.TransientModel):
    _inherit = "asset.depreciation.confirmation.wizard"

    post_entries = fields.Boolean(string="Post Journal Entries")

    # replace the method adding post_move parameter to context
    @api.multi
    def asset_compute(self):
        self.ensure_one()
        context = self._context
        created_move_ids = self.env['account.asset.asset'].with_context(post_move=self.post_entries).\
            compute_generated_entries(self.date, asset_type=context.get('asset_type'))

        return {
            'name': _('Created Asset Moves') if context.get('asset_type') == 'purchase' else _('Created Revenue Moves'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'domain': "[('id','in',[" + ','.join(map(str, created_move_ids)) + "])]",
            'type': 'ir.actions.act_window',
        }
