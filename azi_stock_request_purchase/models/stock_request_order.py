from odoo import models, _
from odoo.exceptions import ValidationError


class StockRequestOrder(models.Model):
    _inherit = 'stock.request.order'

    def launch_procure_specific_requests(self):
        for record in self:
            stock_requests = record.stock_request_ids.filtered(lambda r: r.to_procure and r.can_edit_procure)
            if not stock_requests:
                raise ValidationError(_('You don\'t have any request to procure'))
            stock_requests._action_launch_procurement_rule()

