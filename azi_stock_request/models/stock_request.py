from odoo import models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class StockRequest(models.Model):
    _inherit = 'stock.request'

    def _action_launch_procurement_rule(self):
        """
        Launch procurement group (if not enough stock is available) run method
        with required/custom fields genrated by a
        stock request. procurement group will launch '_run_move',
        '_run_buy' or '_run_manufacture'
        depending on the stock request product rule.
        """
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        errors = []
        for request in self:
            if request._skip_procurement():
                continue
            qty = 0.0
            for move in request.move_ids.filtered(lambda r: r.state != "cancel"):
                qty += move.product_qty

            if float_compare(qty, request.product_qty, precision_digits=precision) >= 0:
                continue

            # If stock is available we use it and we do not execute rule
            if request.company_id.stock_request_check_available_first:
                if (
                    float_compare(
                        request.product_id.sudo()
                        .with_context(location=request.location_id.id)
                        .free_qty,
                        request.product_uom_qty,
                        precision_digits=precision,
                    )
                    >= 0
                ):
                    request._action_use_stock_available()
                    continue

            values = request._prepare_procurement_values(
                group_id=request.procurement_group_id
            )
            try:
                procurements = []
                procurements.append(
                    self.env["procurement.group"].Procurement(
                        request.product_id,
                        request.product_uom_qty,
                        request.product_uom_id,
                        request.location_id,
                        request.name,
                        request.name,
                        self.env.company,
                        values,
                    )
                )
                # Modified the context
                self.env["procurement.group"].with_context(active_model='stock.request', stock_request_id=request.id).run(procurements)
            except UserError as error:
                errors.append(error.name)
        if errors:
            raise UserError("\n".join(errors))
        return True
