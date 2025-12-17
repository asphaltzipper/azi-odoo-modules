from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockQuant(models.Model):
    _inherit = "stock.quant"

    inventory_value = fields.Float(
        string='Unit Value',
    )

    @api.onchange('inventory_quantity', 'quantity', 'inventory_value')
    def _onchange_quantity(self):
        if self.quantity >= self.inventory_quantity and self.inventory_value > 0:
            raise ValidationError(_(
                'In case quantity is greater than counted quantity, you can not set inventory value.'))

    @api.model
    def _get_inventory_fields_create(self):
        allowed_fields = super(StockQuant, self)._get_inventory_fields_create()
        allowed_fields.append('inventory_value')
        return allowed_fields

    def _apply_inventory(self):
        # TODO: make this more efficient by operating on all quants at once
        for quant in self:
            is_quant = quant.inventory_quantity > quant.quantity and True
            quant = quant.with_context(is_quant=is_quant, inventory_value=quant.inventory_value)
            super(StockQuant, quant)._apply_inventory()
            quant.write({'inventory_value': 0})

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
