# Copyright 2024 John Welch
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockQuant(models.Model):
    _inherit = "stock.quant"

    inventory_value = fields.Float('Inventory Value')
    category_id = fields.Many2one(
        comodel_name='product.category',
        related='product_id.categ_id',
        readonly=True,
        store=True)

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
        is_quant = self.inventory_quantity > self.quantity and True
        self = self.with_context(is_quant=is_quant, inventory_value=self.inventory_value)
        super(StockQuant, self)._apply_inventory()
        self.write({'inventory_value': 0})

    def action_print_report(self):
        records = self
        if 'active_domain' in self.env.context:
            records = self.search(self.env.context['active_domain'])
        return self.env['ir.actions.report'].search(
            [('report_name', '=', 'azi_stock.report_stock_quant')]).report_action(records, config=False)
