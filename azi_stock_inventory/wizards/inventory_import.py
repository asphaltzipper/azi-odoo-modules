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

    name = fields.Char(
        string='Name',
    )
    location_id = fields.Many2one('stock.location', 'Inventoried Location', default=_default_location_id)
    data_file = fields.Binary('Inventory File')
    filename = fields.Char('Filename')

    def import_inventory_adjustment(self):
        wb = open_workbook(file_contents=base64.decodebytes(self.data_file))
        sheet = wb.sheets()[0]
        column_names = ('product_id', 'counted_qty', 'unit_value', 'lot_name')
        column_pos = dict([(sheet.cell(0, i).value, i) for i in range(sheet.ncols)
                          if sheet.cell(0, i).value in column_names])
        if 'product_id' not in column_pos or 'counted_qty' not in column_pos:
            raise ValidationError('Sorry, make sure to have `product_id` and `counted_qty` in xlsx header')

        # parse the file data
        product_col = column_pos['product_id']
        qty_col = column_pos['counted_qty']
        value_col = column_pos.get('unit_value')
        lot_col = column_pos.get('lot_name')
        unique_adjustments = set()
        adjustments = []
        duplicates = set()
        product_ids = set()
        for row in range(1, sheet.nrows):
            prod_ref = sheet.cell(row, product_col).value
            product = self.env['product.product'].search([('default_code', '=', prod_ref)], limit=1)
            if not product:
                raise ValidationError(_("Product %s doesn't exist", prod_ref))
            qty = sheet.cell(row, qty_col).value
            if qty in (None, ''):
                raise ValidationError(_("No quantity specified for product %s", prod_ref))
            lot_ref = lot_col and sheet.cell(row, lot_col).value
            if not isinstance(lot_ref, str):
                try:
                    lot_ref = str(int(lot_ref))
                except:
                    raise ValidationError(_("Lot/serial must be text: %s", lot_ref))
            if lot_ref and product.tracking == 'none':
                raise ValidationError(_("Lot/serial %s was specified for untracked product %s", lot_ref, prod_ref))
            if product.tracking != 'none' and not lot_ref:
                raise ValidationError(_("No lot/serial was specified for tracked product %s", prod_ref))
            lot = lot_ref and self.env['stock.lot'].search([('name', '=', lot_ref), ('product_id', '=', product.id)]) or False
            if lot_ref and not lot:
                raise ValidationError(_("Lot %s doesn't exist for product %s", lot_ref, prod_ref))
            value = value_col and sheet.cell(row, value_col).value

            # check for duplicate adjustments
            if (product.id, lot and lot.id) in unique_adjustments:
                duplicates.add((prod_ref, lot_ref or False))
            else:
                adjustments.append({
                    'product_id': product.id,
                    'quantity': qty,
                    'value': value,
                    'lot_id': lot and lot.id,
                })
            unique_adjustments.add((product.id, lot and lot.id))
            product_ids.add(product.id)

        # handle duplicate adjustments
        if duplicates:
            raise ValidationError(_("Found %s duplicated adjustments", len(duplicates)))
        if not adjustments:
            raise ValidationError(_("Found no valid adjustments in the imported file"))

        inventory_vals = {
            'location_ids': [[6, False, [self.location_id.id]]],
            'name': self.name or self.filename,
            'imported': True,
            'product_selection': 'manual',
            'product_ids': [[6, False, list(product_ids)]],
        }
        inventory = self.env['stock.inventory'].create(inventory_vals)
        inventory.action_state_to_in_progress()

        new_quants = self.env['stock.quant'].browse()
        for adjustment in adjustments:
            update_quant = self.env['stock.quant'].search([
                ('current_inventory_id', '=', inventory.id),
                ('product_id', '=', adjustment['product_id']),
                ('lot_id', '=', adjustment['lot_id']),
            ])
            if not update_quant:
                update_quant = self.env['stock.quant'].create({
                    'product_id': adjustment['product_id'],
                    'lot_id': adjustment['lot_id'],
                    'location_id': inventory.location_ids[0].id,
                    'to_do': True,
                    'user_id': inventory.responsible_id,
                    'inventory_date': inventory.date,
                    'current_inventory_id': inventory.id,
                    'inventory_value': adjustment['value'] or False,
                })
                new_quants |= update_quant
            # update_quant.update({
            #     'inventory_quantity': adjustment['quantity'],
            #     'inventory_value': adjustment['value'],
            # })
            update_quant.inventory_quantity = adjustment['quantity']
            update_quant.inventory_value = adjustment['value']
            # update_quant.inventory_diff_quantity = update_quant.inventory_quantity - update_quant.quantity
            # update_quant.inventory_quantity_set = True
            # update_quant.user_id = inventory.responsible_id.id

        quants = inventory._get_quants(inventory.location_ids)
        # inventory.write({'stock_quant_ids': [(6, 0, quants.ids + new_quants.ids)]})
        inventory.write({'stock_quant_ids': [(6, 0, quants.ids)]})
        # self.env.all.tocompute[self.env['stock.quant']._fields['inventory_diff_quantity']].update(inventory.stock_quant_ids.ids)
        # self.env['stock.quant'].recompute()

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
