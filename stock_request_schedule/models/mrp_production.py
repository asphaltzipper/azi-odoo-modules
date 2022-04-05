from odoo import models, api


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.multi
    def action_cancel(self):
        res = super(MrpProduction, self).action_cancel()
        for production in self:
            if production.stock_request_ids:
                production.stock_request_ids.action_draft()
        return res
