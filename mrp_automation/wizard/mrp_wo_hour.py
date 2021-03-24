from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class MrpWoHour(models.TransientModel):
    _name = 'mrp.wo.hour'
    _description = "Production Line Hours Entry"

    produce_id = fields.Many2one('mrp.wo.produce', 'MRP Produce')
    work_order_line = fields.Many2one('mrp.wo.produce.work_line', 'Work Order')
    quantity = fields.Float('Quantity')
    quantity_to_produce = fields.Float('Quantity to Produce', related='produce_id.production_id.product_qty')
    no_of_hours = fields.Float('Number of Hours')

    def set_hours_of_wo(self):
        if not self.quantity:
            raise ValidationError(_('Please set a value for quantity'))
        if self.quantity != self.quantity_to_produce:
            self.produce_id.update({'update_quantity': True, 'new_quantity': self.quantity})
        self.work_order_line.update({'labor_time': self.no_of_hours})
        view_id = self.env.ref('mrp_wo_produce.view_mrp_wo_produce_wizard').id
        return {'type': 'ir.actions.act_window',
                'name': _('Wo Produce'),
                'res_model': 'mrp.wo.produce',
                'target': 'current',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': self.produce_id.id,
                'context': {'form_view_initial_mode': 'edit', 'barcode_scan': True},
                'views': [[view_id, 'form']],
                }
