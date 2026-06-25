from odoo import models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _post_inventory(self, cancel_backorder=False):
        self = self.with_context(active_model='mrp.production')
        return super(MrpProduction, self)._post_inventory(cancel_backorder=cancel_backorder)
