from odoo import api, fields, models, _
from odoo.exceptions import UserError


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

    @api.depends("stock_request_ids.state")
    def _compute_state(self):
        for item in self:
            states = item.stock_request_ids.mapped("state")
            if not item.stock_request_ids or all(x == "draft" for x in states):
                item.state = "draft"
            elif all(x == "cancel" for x in states):
                item.state = "cancel"
            elif all(x in ("done", "cancel") for x in states):
                item.state = "done"
            elif any(x == "submitted" for x in states):
                item.state = "submitted"
            else:
                item.state = "open"

    def action_confirm(self):
        if not self.stock_request_ids:
            raise UserError(
                _("There should be at least one request item for confirming the order.")
            )
        self.mapped("stock_request_ids").filtered(lambda x: x.state in ["draft", "submitted"]).action_confirm()
        return True
