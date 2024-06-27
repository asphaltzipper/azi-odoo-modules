from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class MrpWoProduce(models.TransientModel):
    _name = "mrp.wo.produce"
    _inherit = ["mrp.wo.produce", "barcodes.barcode_events_mixin"]

    update_quantity = fields.Boolean('Update Quantity')
    new_quantity = fields.Float('New Quantity to Produce')

    def do_produce(self):
        if self.update_quantity:
            change_mo_qty = self.env['change.production.qty'].create({'mo_id': self.production_id.id,
                                                                      'product_qty': self.new_quantity})
            change_mo_qty.change_prod_qty()
        action = super(MrpWoProduce, self).do_produce()
        if self._context.get('barcode_scan', False):
            view_id = self.env.ref('mrp.mrp_production_form_view').id
            action = {
                'type': 'ir.actions.act_window',
                'name': _('Manufacturing Order'),
                'res_model': 'mrp.production',
                'target': 'current',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': self.production_id.id,
                'views': [[view_id, 'form']],

            }
        return action

    def barcode_scanned_action(self, barcode):
        employee = self.env['hr.employee'].sudo().search([('barcode', '=', barcode)], limit=1)
        if employee and employee.user_id:
            work_line_ids = self.work_line_ids.filtered(lambda w: not w.user_id)
            if work_line_ids:
                work_line_ids[0].update({'user_id': employee.user_id})
                view_id = self.env.ref('mrp_automation.view_mrp_wo_hour_form').id
                return {'type': 'ir.actions.act_window',
                        'name': _('Wo Hour'),
                        'res_model': 'mrp.wo.hour',
                        'target': 'new',
                        'view_mode': 'form',
                        'view_type': 'form',
                        'context': {'default_produce_id': self.id, 'default_work_order_line': work_line_ids[0].id},
                        'views': [[view_id, 'form']],
                        }
            raise ValidationError("There is no work order associated to this production")
        raise ValidationError(_("Please scan the correct barcode for employee or check that "
                                "employee is linked to a user"))
