# Copyright 2024 John Welch
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockQuant(models.Model):
    _inherit = "stock.quant"

    inventory_value = fields.Float('Unit Value')
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
        # TODO: make this more efficient by operating on all quants at once
        for quant in self:
            is_quant = quant.inventory_quantity > quant.quantity and True
            quant = quant.with_context(is_quant=is_quant, inventory_value=quant.inventory_value)
            super(StockQuant, quant)._apply_inventory()
            quant.write({'inventory_value': 0})

    def action_print_report(self):
        records = self
        if 'active_domain' in self.env.context:
            records = self.search(self.env.context['active_domain'])
        return self.env['ir.actions.report'].search(
            [('report_name', '=', 'azi_stock.report_stock_quant')]).report_action(records, config=False)

    def _set_stock_valuation_filter(self):
        current_year = datetime.datetime.now().year
        quant_filter = self.env['ir.filters'].search([('model_id', '=', 'stock.quant'),
                                                      ('name', 'ilike', current_year)])
        action = self.env.ref('azi_stock.fg_quantsact')
        if not quant_filter:
            for i in range(1, 13):
                domain_list = [["product_id.type", "=", "product"], ["quantity", ">", 0], ["lot_id", "!=", False],
                               ["category_id", "ilike", "FG "]]
                date_from = f'{current_year}-{i:02d}-01 00:00:00'
                date_to = f'{current_year}-{i+1:02d}-01 00:00:00'
                if i == 12:
                    date_to = f'{current_year+1}-01-01 00:00:00'
                name = f'{current_year}-{i:02d} Build'
                domain_list.extend([["in_date", "<", date_to], ["in_date", ">=", date_from]])
                self.env['ir.filters'].create({'model_id': 'stock.quant', 'action_id': action.id, 'name': name,
                                               'context': {u'group_by': [u'category_id']}, 'domain': domain_list,
                                               'sort': '["lot_id"]'})
