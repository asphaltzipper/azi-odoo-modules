# -*- coding: utf-8 -*-

from odoo import api, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.multi
    def action_assign(self):
        for production in self:
            move_to_assign = production.move_raw_ids.filtered(lambda x: x.state == 'draft')
            warehouse_id = self.location_src_id.get_warehouse().id
            for move in move_to_assign:
                loc = move.product_id.property_stock_production
                move.warehouse_id = warehouse_id
                move.location_dest_id = loc
            move_to_assign.action_confirm()
        return super(MrpProduction, self).action_assign()
