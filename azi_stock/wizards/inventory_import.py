from xlrd import open_workbook
import base64

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InventoryImport(models.TransientModel):
    _name = 'inventory.import'
    _description = 'Import inventory'

    @api.model
    def _default_location_id(self):
        company_user = self.env.user.company_id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_user.id)], limit=1)
        if warehouse:
            return warehouse.lot_stock_id.id

    location_id = fields.Many2one('stock.location', 'Inventoried Location', default=_default_location_id)
    data_file = fields.Binary('Inventory File')
    filename = fields.Char('Filename')

    def import_inventory_adjustment(self):
        wb = open_workbook(file_contents=base64.decodebytes(self.data_file))
        sheet = wb.sheets()[0]
        column_pos = dict([(sheet.cell(0, i).value, i) for i in range(sheet.ncols)
                          if sheet.cell(0, i).value in ('product_id', 'counted_qty')])
        if 'product_id' not in column_pos or 'counted_qty' not in column_pos:
            raise ValidationError('Sorry, make sure to have `product_id` and `counted_qty` in xlsx header')
        product_col = column_pos['product_id']
        qty_col = column_pos['counted_qty']
        product_adjustment = {}
        for row in range(1, sheet.nrows):
            prod_ref = sheet.cell(row, product_col).value
            qty = sheet.cell(row, qty_col).value
            product = self.env['product.product'].search([('default_code', '=', prod_ref)], limit=1)
            if product and qty is not None:
                product_adjustment.update({product.id: qty})
            else:
                raise ValidationError(f"Bad Part Number or Quantity: {prod_ref}, {qty}")

        inventory_vals = {'location_ids': [[6, False, [self.location_id.id]]], 'name': self.filename,
                          'imported': True, 'product_selection': 'manual'}
        if product_adjustment:
            inventory_vals['product_ids'] = [[6, False, list(product_adjustment.keys())]]
        inventory = self.env['stock.inventory'].create(inventory_vals)
        inventory.action_state_to_in_progress()
        for quant in inventory.stock_quant_ids:
            qty_to_adjust = product_adjustment.get(quant.product_id.id)
            if qty_to_adjust:
                quant.inventory_quantity = qty_to_adjust
        view_id = self.env.ref('stock_inventory.view_inventory_group_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Inventory Adjustments',
            'res_model': 'stock.inventory',
            'target': 'current',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': inventory.id,
            'view_id': view_id,
            'views': [[view_id, 'form']],
        }
