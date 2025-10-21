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
        if len(self.product_ids) != len(self.stock_quant_ids.mapped('product_id')):
            quant_product = self.stock_quant_ids.mapped('product_id')
            quant_ids = set()
            for product in self.product_ids:
                if product not in quant_product:
                    quant = self.env['stock.quant'].create({'product_id': product.id,
                                                            'location_id': self.location_ids[0].id,
                                                            'to_do': True,
                                                            'user_id': self.responsible_id,
                                                            'inventory_date': self.date,
                                                            'current_inventory_id': self.id,
                                                            })
                    quant_ids.add(quant.id)
            quants = self._get_quants(self.location_ids)
            quant_ids.update(quants.ids)
            self.write({'stock_quant_ids': [(6, 0, quant_ids)]})

    def action_view_inventory_adjustment(self):
        return super(InventoryAdjustmentsGroup, self.with_context(inventory_adjustment=True)).action_view_inventory_adjustment()

    def action_state_to_done(self):
        self.stock_quant_ids.action_apply_inventory()
        res = super(InventoryAdjustmentsGroup, self).action_state_to_done()
        zero_quants = self.stock_quant_ids.filtered(lambda q: q.quantity == q.inventory_quantity == 0)
        zero_quants.sudo().unlink()
        return res
