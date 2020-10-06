# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class MrpProduction(models.Model):
    _name = "mrp.production"
    _inherit = ["mrp.production", "barcodes.barcode_events_mixin"]

    @api.multi
    def open_wo_produce(self):
        self.ensure_one()
        action = self.env.ref('mrp_wo_produce.act_mrp_wo_produce_wizard').read()[0]
        return action

    @api.multi
    def new_wo_produce(self):
        self.ensure_one()
        mrp_wo = self.env['mrp.wo.produce'].with_context({'default_production_id': self.id}).create({})
        mrp_wo.load_lines()
        view_id = self.env.ref('mrp_wo_produce.view_mrp_wo_produce_wizard').id
        return {'type': 'ir.actions.act_window',
                'name': _('Wo Produce'),
                'res_model': 'mrp.wo.produce',
                'target': 'current',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': mrp_wo.id,
                'context': {'form_view_initial_mode': 'edit', 'barcode_scan': True},
                'views': [[view_id, 'form']],
                }

    @api.multi
    def post_inventory(self):
        for order in self:
            # The default behavior is to cancel stock moves when the serial number is not specified
            # We don't want to allow the user to post inventory without specifying a serial number for all tracked
            # components.  If we are going to build without the tracked component, then cancel the stock move.  If we
            # actually have the component, then do an inventory adjustment or something.
            serial_moves = order.move_raw_ids\
                .filtered(lambda x: x.state not in ('done', 'cancel') and x.product_id.tracking == 'serial')
            for move_lot in serial_moves.mapped('active_move_line_ids'):
                if not move_lot.lot_id or not move_lot.qty_done:
                    raise UserError(_('You should provide a lot for a component'))
        return super(MrpProduction, self).post_inventory()

    def barcode_scanned_action(self, barcode):
        if self.name == barcode:
            mrp_wo = self.env['mrp.wo.produce'].with_context({'default_production_id': self.id}).create({})
            mrp_wo.load_lines()
            view_id = self.env.ref('mrp_wo_produce.view_mrp_wo_produce_wizard').id
            return {'type': 'ir.actions.act_window',
                    'name': _('Wo Produce'),
                    'res_model': 'mrp.wo.produce',
                    'target': 'current',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_id': mrp_wo.id,
                    'context': {'form_view_initial_mode': 'edit', 'barcode_scan': True},
                    'views': [[view_id, 'form']],
                    }
        barcode_split = barcode.split(',')
        if barcode_split and len(barcode_split) == 2:
            try:
                barcode_product, barcode_qty = barcode_split
                product_id = int(barcode_product)
                kit_count = int(float(barcode_qty))
                product_id = self.env['product.product'].browse(product_id)
                product_qty = float(barcode_qty)
            except:
                raise UserError(_("Failed to get product ID and quantity from barcode:\n%s" % barcode))

            # compare number of available kits
            if product_id.mfg_kit_qty != kit_count:
                message = _("The scanned kit quantity doesn't match kits available:\n"
                            "Available=%s\nScanned=%s" %
                            (product_id.mfg_kit_qty, kit_count))
                self.env.user.notify_warning(message=message, title=product_id.default_code, sticky=True)

            production = self.env['mrp.production']
            mrp_inventory = self.env['mrp.inventory'].search(
                [('product_id', '=', product_id.id), ('to_procure', '>', 0)],
                order='order_release_date', limit=1)

            if mrp_inventory:
                inventory_procure = self.env['mrp.inventory.procure'].with_context({
                    'active_ids': mrp_inventory.ids,
                    'active_model': 'mrp.inventory'
                }).create({})
                if len(inventory_procure.item_ids) != 1:
                    raise UserError(_("Too many planned orders were selected. We can only create a "
                                      "single MO from a kit."))
                inventory_procure.make_procurement()
                productions = inventory_procure.item_ids.planned_order_id.mrp_production_ids
                production = productions.sorted(key=lambda x: x.name, reverse=True)[0]
                if production.product_uom_qty != product_qty:
                    message = _("The scanned kit quantity doesn't match the planned order quantity:\n"
                                "Planned=%s\nScanned=%s" %
                                (production.product_uom_qty, product_qty))
                    self.env.user.notify_warning(message=message, title=product_id.default_code, sticky=True)
                qty_wiz = self.env['change.production.qty'].create({
                    'mo_id': production.id, 'product_qty': product_qty})
                qty_wiz.change_prod_qty()
            else:
                message = _("No planned orders were found. You may not need this MO.")
                self.env.user.notify_warning(message=message, title=product_id.default_code, sticky=True)
                picking_type = production._get_default_picking_type()
                bom = product_id.bom_ids and product_id.bom_ids[0] or self.env['mrp.bom']
                if bom.type != 'normal':
                    raise UserError(_("This product has a phantom BOM.  We can't make an MO."))
                production_vals = {
                    'picking_type_id': picking_type,
                    'product_id': product_id.id,
                    'product_qty': product_qty,
                    'product_uom_id': product_id.uom_id.id,
                    'bom_id': bom.id,
                    'date_planned_finished': fields.Datetime.now(),
                }
                production = production.create(production_vals)

            production.action_assign()
            production.button_plan()
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

        raise ValidationError(_("Please scan the correct barcode"))
