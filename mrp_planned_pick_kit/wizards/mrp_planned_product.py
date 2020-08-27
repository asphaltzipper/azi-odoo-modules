from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MrpPlannedProduct(models.TransientModel):
    _name = "mrp.planned.product"
    _inherit = "barcodes.barcode_events_mixin"

    product_id = fields.Many2one('product.product')

    def on_barcode_scanned(self, barcode):
        self.product_id = self.env['product.product'].search([('barcode', '=', barcode)])
        if not self.product_id:
            raise UserError(_('There is no product assigned to this barcode'))
        productions = []
        mrp_inventory = self.env['mrp.inventory'].search([('product_id', '=', self.product_id.id),
                                                          ('to_procure', '>', 0)])
        if mrp_inventory:
            inventory_procure = self.env['mrp.inventory.procure'].with_context({'active_ids': mrp_inventory.ids,
                                                                                'active_model': 'mrp.inventory'}).\
                create({})
            inventory_procure.make_procurement()
            for item in inventory_procure.item_ids:
                mrp_productions = item.planned_order_id.mrp_production_ids
                productions.extend(mrp_productions.ids)
                mrp_productions.action_assign()
                mrp_productions.button_plan()
        else:
            production_obj = self.env['mrp.production']
            picking_type = production_obj._get_default_picking_type()
            production_vals = {'picking_type_id': picking_type, 'product_id': self.product_id.id}
            bom = self.env['mrp.bom']._bom_find(product=self.product_id,
                                                picking_type=self.env['stock.picking.type'].browse(picking_type),
                                                company_id=self.env.user.company_id.id)
            if bom.type == 'normal':
                production_vals.update(bom_id=bom.id, product_qty=bom.product_qty, product_uom_id=bom.product_uom_id.id,
                                       date_planned_finished=fields.Datetime.now())
                production = production_obj.create(production_vals)
                production.action_assign()
                production.button_plan()
                productions.append(production.id)

