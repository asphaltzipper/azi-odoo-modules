from odoo import models, api, fields, _
from odoo.exceptions import UserError


class MrpAutomation(models.TransientModel):
    _name = 'mrp.automation'
    _inherit = 'barcodes.barcode_events_mixin'
    _description = 'Automate MO'

    scan_error = fields.Boolean('Barcode Error')
    scan_name = fields.Char('Barcode Value')

    def get_produce_wizard(self, production):
        mrp_wo = self.env['mrp.wo.produce'].with_context({'default_production_id': production.id}).create({})
        mrp_wo.load_lines()
        return mrp_wo

    def convert_kit(self, product, kit_count):
        production = self.env['mrp.production']
        product_qty = float(kit_count)

        # compare number of available kits
        if product.mfg_kit_qty != kit_count:
            message = _("The scanned kit quantity doesn't match kits available:\n"
                        "Available=%s\nScanned=%s" %
                        (product.mfg_kit_qty, kit_count))
            self.env.user.notify_warning(message=message, title=product.default_code, sticky=True)

        # find planned orders
        mrp_inventory = self.env['mrp.inventory'].search(
            [('product_id', '=', product.id), ('to_procure', '>', 0)],
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
            if production.product_uom_qty != product_qty:
                message = _("The scanned kit quantity doesn't match the planned order quantity:\n"
                            "Planned=%s\nScanned=%s" %
                            (production.product_uom_qty, product_qty))
                self.env.user.notify_warning(message=message, title=product.default_code, sticky=True)
            qty_wiz = self.env['change.production.qty'].create({
                'mo_id': production.id, 'product_qty': product_qty})
            qty_wiz.change_prod_qty()
        else:
            message = _("No planned orders were found. You may not need this MO.")
            self.env.user.notify_warning(message=message, title=product.default_code, sticky=True)
            picking_type = production._get_default_picking_type()
            bom = product.bom_ids and product.bom_ids[0] or self.env['mrp.bom']
            if bom.type != 'normal':
                raise UserError(_("This product has a phantom BOM.  We can't make an MO."))
            production_vals = {
                'picking_type_id': picking_type,
                'product_id': product.id,
                'product_qty': product_qty,
                'product_uom_id': product.uom_id.id,
                'bom_id': bom.id,
                'date_planned_finished': fields.Datetime.now(),
            }
            production = production.create(production_vals)

        production.action_assign()
        production.button_plan()
        production.direct_print_azi_report()
        return production


    def barcode_scanned_action(self, barcode):

        # try recognizing the scanned barcode
        scan_mo = self.env['mrp.production'].search([('name', '=', barcode)])
        product = self.env['product.product']
        kit_count = 0
        try:
            barcode_product, barcode_qty = barcode.split(',')
            product_id = int(barcode_product)
            kit_count = int(float(barcode_qty))
            product = self.env['product.product'].browse(product_id)
        except:
            pass

        # return an appropriate action
        if scan_mo:
            produce_wiz = self.get_produce_wizard(scan_mo)
            view_id = self.env.ref('mrp_wo_produce.view_mrp_wo_produce_wizard').id
            return {
                'type': 'ir.actions.act_window',
                'name': _('Wo Produce'),
                'res_model': 'mrp.wo.produce',
                'target': 'current',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': produce_wiz.id,
                'context': {'form_view_initial_mode': 'edit', 'barcode_scan': True},
                'views': [[view_id, 'form']],
            }
        elif product:
            if product.deprecated:
                raise UserError(_("This kit is obsolete. If you really want to produce an obsolete part, create the "
                                  "MO manually."))
            production = self.convert_kit(product, kit_count)
            view_id = self.env.ref('mrp.mrp_production_form_view').id
            return {
                'type': 'ir.actions.act_window',
                'name': _('Manufacturing Order'),
                'res_model': 'mrp.production',
                'target': 'current',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': production.id,
                'views': [[view_id, 'form']],
            }
        else:
            mrp_automation = self.create({'scan_error': True, 'scan_name': barcode})
            view_id = self.env.ref('mrp_automation.mrp_automation_form').id
            return {
                'type': 'ir.actions.act_window',
                'name': _('MO Automation'),
                'res_model': 'mrp.automation',
                'target': 'current',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': mrp_automation.id,
                'context': {'form_view_initial_mode': 'edit', 'barcode_scan': True},
                'views': [[view_id, 'form']],
            }
