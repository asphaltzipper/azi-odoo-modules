from odoo import api, fields, models, _


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_done(self, cancel_backorder=False):
        self = self.with_context(move=self)
        res = super(StockMove, self)._action_done(cancel_backorder=cancel_backorder)
        return res
