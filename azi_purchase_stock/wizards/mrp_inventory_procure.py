from odoo import api, models, tools, _
from odoo.exceptions import UserError, ValidationError


class MrpInventoryProcure(models.TransientModel):
    _inherit = 'mrp.inventory.procure'

    @api.multi
    def make_procurement(self):
        self.ensure_one()
        errors = []
        for item in self.item_ids:
            if not item.qty:
                raise ValidationError(_("Quantity must be positive."))
            values = item._prepare_procurement_values()
            # Run procurement
            try:
                # Add context
                self.env['procurement.group'].with_context(procure_wizard=True).run(
                    item.product_id,
                    item.qty,
                    item.uom_id,
                    item.location_id,
                    'INT: ' + str(self.env.user.login),  # name?
                    'INT: ' + str(self.env.user.login),  # origin?
                    values
                )
                item.planned_order_id.qty_released += item.qty
            except UserError as error:
                errors.append(error.name)
            if errors:
                raise UserError('\n'.join(errors))
        return {'type': 'ir.actions.act_window_close'}
