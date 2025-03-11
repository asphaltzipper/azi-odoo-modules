from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class InventoryAdjustmentsGroup(models.Model):
    _inherit = "stock.inventory"

    def action_state_to_in_progress(self):
        if self.product_selection == "manual" and not self.product_ids:
            raise UserError(_(
                "You must select products to adjust before "
                "beginning Manual Selection adjustments"
            ))
        super(InventoryAdjustmentsGroup, self).action_state_to_in_progress()
