from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class InventoryAdjustmentsGroup(models.Model):
    _inherit = "stock.inventory"

    imported = fields.Boolean(
        string='Imported',
    )

    product_selection = fields.Selection(
        default="manual",
    )

    def action_state_to_draft(self):
        self.ensure_one()
        self.stock_quant_ids.action_set_inventory_quantity_to_zero()
        # self.stock_quant_ids.update({
        #     "inventory_quantity": False,
        #     "inventory_quantity_set": False,
        # })
        return super(InventoryAdjustmentsGroup, self).action_state_to_draft()

    def action_state_to_in_progress(self):
        if self.product_selection == "manual" and not self.product_ids:
            raise UserError(_(
                "You must select products to adjust before "
                "beginning Manual Selection adjustments"
            ))
        super(InventoryAdjustmentsGroup, self).action_state_to_in_progress()
        quant_products = self.stock_quant_ids.mapped('product_id')
        untracked_products = self.product_ids.filtered(lambda p: p.tracking == "none")
        new_quant_products = untracked_products - quant_products
        if new_quant_products:
            new_quants = self.env['stock.quant']
            for product in new_quant_products:
                new_quants |= self.env['stock.quant'].create({
                    'product_id': product.id,
                    'location_id': self.location_ids[0].id,
                    'to_do': True,
                    'user_id': self.responsible_id,
                    'inventory_date': self.date,
                    'current_inventory_id': self.id,
                })
            quants = self._get_quants(self.location_ids)
            self.write({'stock_quant_ids': [(6, 0, quants.ids + new_quants.ids)]})

    def action_view_inventory_adjustment(self):
        return super(InventoryAdjustmentsGroup, self.with_context(inventory_adjustment=True)).action_view_inventory_adjustment()

    def action_state_to_done(self):
        unset_lines = self.stock_quant_ids.filtered(lambda x: not x.inventory_quantity_set)
        if unset_lines:
            raise ValidationError(_(
                "Counted quantity must be set on all lines before completing the"
                " inventory: %s line(s) unset", len(unset_lines)
            ))
        self.stock_quant_ids.action_apply_inventory()
        res = super(InventoryAdjustmentsGroup, self).action_state_to_done()
        zero_quants = self.stock_quant_ids.filtered(lambda q: q.quantity == q.inventory_quantity == 0)
        zero_quants.sudo().unlink()
        return res

    def unlink(self):
        if self.filtered(lambda i: i.state != 'draft'):
            raise ValidationError(_("Set state to draft before deleting"))
        return super(InventoryAdjustmentsGroup, self).unlink()
