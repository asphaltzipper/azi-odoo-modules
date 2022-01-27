from datetime import date
from odoo import fields, models, _


class WizardStockRequestOrderKanban(models.TransientModel):
    _inherit = "wizard.stock.request.kanban"

    def barcode_ending(self):
        self.kanban_id.write({'verify_date': date.today()})
        stock_request = self.env['stock.request'].search([('kanban_id',  '=', self.kanban_id.id), ('state', 'not in', ('done', 'cancel'))])
        if stock_request:
            for request in stock_request:
                request.order_id.write({'request_ids':  [(4, request.id)]})
        else:
            self.stock_request_id = self.env['stock.request'].create(
                self.stock_request_kanban_values()
            )
            self.status_state = 0
            self.status = _('Added kanban %s for product %s' % (
                self.stock_request_id.kanban_id.name,
                self.stock_request_id.product_id.display_name
            ))
            self.stock_request_ending()
        self.order_id = self.stock_request_id.order_id
