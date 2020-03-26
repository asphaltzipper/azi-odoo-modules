from odoo import models, fields, api, _


class StockMove(models.Model):
    _inherit = "stock.move"

    def action_assign(self):
        for move in self:
            move._action_assign()

    def do_unreserve(self):
        for move in self:
            move._do_unreserve()
