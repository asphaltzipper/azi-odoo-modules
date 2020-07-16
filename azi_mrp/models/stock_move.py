# -*- coding: utf-8 -*-

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    # add the store attribute to the has_tracking field
    # Odoo will likely rename this field in a later version
    # TODO: change name to match odoo's new name when upgrading to the next version
    has_tracking = fields.Selection(
        related='product_id.tracking',
        string='Product with Tracking',
        store=True)

    def action_view_manufacturing_order(self):
        action = self.env.ref('mrp.mrp_production_action').read()[0]
        action['domain'] = [('product_id', '=', self.product_id.id)]
        action['context'] = {'search_default_todo': 1}
        return action
