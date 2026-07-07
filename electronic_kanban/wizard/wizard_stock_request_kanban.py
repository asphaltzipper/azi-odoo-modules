from datetime import date
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class WizardStockRequestOrderKanban(models.TransientModel):
    _inherit = "wizard.stock.request.kanban"

    def barcode_ending(self):
        self.kanban_id.write({'verify_date': date.today()})
        other_requests = self.env['stock.request'].search([
            ('kanban_id', '=', self.kanban_id.id),
            ('state', 'not in', ('done', 'cancel')),
        ], limit=1)
        if other_requests:
            raise ValidationError(_(
                "Kanban %s already has an open stock request", self.kanban_id.name
            ))
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
