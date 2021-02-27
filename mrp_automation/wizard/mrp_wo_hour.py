from odoo import models, api, fields, _


class MrpWoHour(models.TransientModel):
    _name = 'mrp.wo.hour'
    _description = "Production Line Hours Entry"

    produce_id = fields.Many2one('mrp.wo.produce', 'MRP Produce')
    work_order_line = fields.Many2one('mrp.wo.produce.work_line', 'Work Order')
    no_of_hours = fields.Float('Number of Hours')

    def set_hours_of_wo(self):
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
