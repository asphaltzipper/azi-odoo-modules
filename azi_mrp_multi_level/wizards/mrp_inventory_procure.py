from odoo import api, models, tools, _
from odoo.exceptions import UserError, ValidationError


class MrpInventoryProcure(models.TransientModel):
    _inherit = 'mrp.inventory.procure'

    def make_procurement(self):
        self.ensure_one()
        errors = []
        pg = self.env["procurement.group"]
        procurements = []
        for item in self.item_ids:
            if not item.qty:
                raise ValidationError(_("Quantity must be positive."))
            values = item._prepare_procurement_values()
            procurements.append(
                pg.Procurement(
                    item.product_id,
                    item.qty,
                    item.uom_id,
                    item.location_id,
                    "MRP: " + (item.planned_order_id.name or self.env.user.login),
                    "MRP: " + (item.planned_order_id.origin or self.env.user.login),
                    item.mrp_inventory_id.company_id,
                    values,
                )
            )
        # Run procurements
        try:
            pg.with_context(mrp_procure=True).run(procurements)
            for item in self.item_ids:
                item.planned_order_id.qty_released += item.qty
        except UserError as error:
            errors.append(error.name)
        if errors:
            raise UserError("\n".join(errors))
        mrp_orders = self.item_ids.mapped('planned_order_id.mrp_production_ids')
        if mrp_orders:
            return{
                'type': 'ir.actions.act_window',
                'name': _('Manufacturing Orders'),
                'res_model': 'mrp.production',
                'target': 'current',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', mrp_orders.ids)]
            }
        return {'type': 'ir.actions.act_window_close'}
