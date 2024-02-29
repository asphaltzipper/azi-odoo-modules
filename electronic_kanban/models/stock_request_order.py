from odoo import api, fields, models, _


class StockRequestOrder(models.Model):
    _inherit = 'stock.request.order'

    def check_done(self):
        for rec in self:
            if not rec.stock_request_ids.filtered(lambda r: r.state not in ['cancel', 'done']):
                rec.action_done()
        return

    def action_check_done(self):
        for rec in self:
            if rec.stock_request_ids.filtered(lambda r: r.state not in ['cancel', 'done']):
                rec.stock_request_ids.check_done()
            if not rec.stock_request_ids.filtered(lambda r: r.state not in ['cancel', 'done']):
                rec.action_done()
            else:
                self.message_post(body="You can not complete the order because some requests are not complete")
        return
