from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductionKitConvert(models.TransientModel):
    _name = "production.kit.convert"
    _description = "Convert production kit to MO"
    _inherit = "barcodes.barcode_events_mixin"

    product_id = fields.Many2one('product.product')
    product_qty = fields.Float()

    def on_barcode_scanned(self, barcode):
        import pdb
        pdb.set_trace()
        try:
            barcode_product, barcode_qty = barcode.split(',')
            product_id = int(barcode_product)
            kit_count = int(float(barcode_qty))
            self.product_id = self.env['product.product'].browse(product_id)
            self.product_qty = float(barcode_qty)
        except:
            raise UserError(_("Failed to get product ID and quantity from barcode:\n%s" % barcode))

        # compare number of available kits
        if self.product_id.mfg_kit_qty != kit_count:
            message = _("The scanned kit quantity doesn't match kits available:\n"
                        "Available=%s\nScanned=%s" %
                        (self.product_id.mfg_kit_qty, kit_count))
            self.env.user.notify_warning(message=message, title=self.product_id.default_code, sticky=True)

        production = self.env['mrp.production']
        mrp_inventory = self.env['mrp.inventory'].search(
            [('product_id', '=', self.product_id.id), ('to_procure', '>', 0)],
            order='order_release_date', limit=1)

        if mrp_inventory:
            inventory_procure = self.env['mrp.inventory.procure'].with_context({
                'active_ids': mrp_inventory.ids,
                'active_model': 'mrp.inventory'
            }).create({})
            if len(inventory_procure.item_ids) != 1:
                raise UserError(_("Too many planned orders were selected. We can only create a single MO from a kit."))
            inventory_procure.make_procurement()
            productions = inventory_procure.item_ids.planned_order_id.mrp_production_ids
            production = productions.sorted(key=lambda x: x.name, reverse=True)[0]
            if production.product_uom_qty != self.product_qty:
                message = _("The scanned kit quantity doesn't match the planned order quantity:\n"
                            "Planned=%s\nScanned=%s" %
                            (production.product_uom_qty, self.product_qty))
                self.env.user.notify_warning(message=message, title=self.product_id.default_code, sticky=True)
            qty_wiz = self.env['change.production.qty'].create({
                'mo_id': production.id, 'product_qty': self.product_qty})
            qty_wiz.change_prod_qty()
        else:
            message = _("No planned orders were found. You may not need this MO.")
            self.env.user.notify_warning(message=message, title=self.product_id.default_code, sticky=True)
            picking_type = production._get_default_picking_type()
            bom = self.product_id.bom_ids and self.product_id.bom_ids[0] or self.env['mrp.bom']
            if bom.type != 'normal':
                raise UserError(_("This product has a phantom BOM.  We can't make an MO."))
            production_vals = {
                'picking_type_id': picking_type,
                'product_id': self.product_id.id,
                'product_qty': self.product_qty,
                'product_uom_id': self.product_id.uom_id.id,
                'bom_id': bom.id,
                'date_planned_finished': fields.Datetime.now(),
            }
            production = production.create(production_vals)

        # if mrp_inventory:
        #     if mrp_inventory.to_procure != self.product_qty:
        #         message = _("The scanned kit quantity doesn't match the next planned order quantity:\n"
        #                     "Planned=%s\nScanned=%s" %
        #                     (production.product_uom_qty, self.product_qty))
        #         self.env.user.notify_warning(message=message, title=self.product_id.default_code, sticky=True)
        # else:
        #     message = _("No planned orders were found. You may not need this MO.")
        #     self.env.user.notify_warning(message=message, title=self.product_id.default_code, sticky=True)
        #
        # picking_type = production._get_default_picking_type()
        # bom = self.product_id.bom_ids and self.product_id.bom_ids[0] or self.env['mrp.bom']
        # if bom.type != 'normal':
        #     raise UserError(_("This product has a phantom BOM.  We can't make an MO."))
        # production_vals = {
        #     'picking_type_id': picking_type,
        #     'product_id': self.product_id.id,
        #     'product_qty': self.product_qty,
        #     'product_uom_id': self.product_id.uom_id.id,
        #     'bom_id': bom.id,
        #     'date_planned_finished': fields.Datetime.now(),
        # }
        # production = production.create(production_vals)

        production.action_assign()
        production.button_plan()
        action = self.env.ref('mrp.mrp_production_action').read()[0]
        action['res_id'] = production.id
        action['target'] = 'current'
        return action
