from odoo import models, fields, api


class MrpInventory(models.Model):
    _inherit = 'mrp.inventory'

    @api.multi
    def action_planned_forecast_detail(self):
        self.ensure_one()
        return self.product_id.action_planned_forecast_detail()
