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
            stock_request_id = self.env["stock.request"].create(
                self.stock_request_kanban_values()
            )
            self.stock_request_id = stock_request_id
            self.stock_request_ending()
            self.update(
                {
                    "status_state": 0,
                    "status": _(
                        "Added kanban %(kanban)s for product %(product)s",
                        kanban=stock_request_id.kanban_id.name,
                        product=stock_request_id.product_id.display_name,
                    ),
                }
            )
