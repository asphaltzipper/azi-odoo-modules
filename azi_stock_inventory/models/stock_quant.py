from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockQuant(models.Model):
    _inherit = "stock.quant"

    inventory_value = fields.Float(
        string='Unit Value',
    )
    inventory_value_set = fields.Boolean(
        string='Set Value',
        default=False,
    )

    @api.onchange('inventory_quantity', 'inventory_value_set', 'inventory_value')
    def _onchange_inventory_value(self):
        if self.quantity >= self.inventory_quantity and self.inventory_value_set:
            self.inventory_value_set = False
            raise ValidationError(_("User specified valuation not allowed on negative adjustments"))

    @api.model
    def _get_inventory_fields_create(self):
        allowed_fields = super(StockQuant, self)._get_inventory_fields_create()
        allowed_fields.extend(['current_inventory_id', 'inventory_value', 'inventory_value_set'])
        return allowed_fields

    def _apply_inventory(self):
        # TODO: make this more efficient by operating on all quants at once
        for quant in self:
            is_quant = quant.inventory_quantity > quant.quantity and quant.inventory_value_set and True
            quant = quant.with_context(is_quant=is_quant, inventory_value=quant.inventory_value)
            super(StockQuant, quant)._apply_inventory()
            quant.write({'inventory_value': 0})

    def action_apply_inventory(self):
        super(StockQuant, self).action_apply_inventory()
        self.inventory_value_set = False

    def action_set_inventory_quantity_to_zero(self):
        super(StockQuant, self).action_set_inventory_quantity_to_zero()
        self.inventory_value = 0
        self.inventory_value_set = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if (
                vals.get('inventory_quantity_set')
                and vals.get('quantity', 0.0) >= vals.get('inventory_quantity', 0.0)
                and vals.get('inventory_value_set')
            ):
                vals['inventory_value_set'] = False
                vals['inventory_value'] = 0

        if (self.env.context.get(
            "active_model", False) == "stock.inventory"
            and self.env.context.get("active_id", False
        )):
            for vals in vals_list:
                vals['current_inventory_id'] = self.env.context.get("active_id")

        return super().create(vals_list)

    def write(self, vals):
        for rec in self:
            if (
                vals.get('inventory_quantity_set', rec.inventory_quantity_set)
                and vals.get('quantity', rec.quantity) >= vals.get('inventory_quantity', rec.inventory_quantity)
                and vals.get('inventory_value_set', rec.inventory_value_set)
            ):
                vals['inventory_value_set'] = False
                vals['inventory_value'] = 0
        return super().write(vals)

    @api.model
    def _quant_tasks(self):
        self._merge_quants()
        if not self.env.context.get('inventory_adjustment', False):
            self._unlink_zero_quants()
