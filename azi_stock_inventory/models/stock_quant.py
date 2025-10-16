from odoo import _, api, fields, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    @api.model
    def _get_inventory_fields_create(self):
        allowed_fields = super(StockQuant, self)._get_inventory_fields_create()
        allowed_fields.append('current_inventory_id')
        return allowed_fields

    @api.model_create_multi
    def create(self, vals_list):
        if (self.env.context.get(
            "active_model", False) == "stock.inventory"
                and self.env.context.get("active_id", False)
        ):
            for vals in vals_list:
                vals['current_inventory_id'] = self.env.context.get("active_id")
        return super().create(vals_list)

    @api.model
    def _quant_tasks(self):
        self._merge_quants()
        if not self.env.context.get('inventory_adjustment', False):
            self._unlink_zero_quants()
