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
        inventory_lines = []
        for row in range(1, sheet.nrows):
            product_id = sheet.cell(row, product_col).value
            qty = sheet.cell(row, qty_col).value
            if product_id and qty:
                inventory_lines.append((0, _, {'product_id': int(product_id), 'location_id': self.location_id.id,
                                               'product_qty': float(qty)}))
        if inventory_lines:
            inventory = self.env['stock.inventory'].create({'location_id': self.location_id.id, 'name': self.filename,
                                                            'imported': True, 'filter': 'partial'})
            inventory.action_start()
            inventory.update({'line_ids': inventory_lines})
