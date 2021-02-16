from odoo import models, api, fields, _


class MrpAutomation(models.TransientModel):
    _name = 'mrp.automation'
    _inherit = 'barcodes.barcode_events_mixin'
    _description = 'Automate MO'

    mo_error = fields.Boolean('No MO exists')
    mo_name = fields.Char('MO Name')

    def barcode_scanned_action(self, barcode):
        mrp_production = self.env['mrp.production'].search([('name', '=', barcode)])
        if mrp_production:
            mrp_wo = self.env['mrp.wo.produce'].with_context({'default_production_id': mrp_production.id}).create({})
            mrp_wo.load_lines()
            view_id = self.env.ref('mrp_wo_produce.view_mrp_wo_produce_wizard').id
            return {
                'type': 'ir.actions.act_window',
                'name': _('Wo Produce'),
                'res_model': 'mrp.wo.produce',
                'target': 'current',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': mrp_wo.id,
                'context': {'form_view_initial_mode': 'edit', 'barcode_scan': True},
                'views': [[view_id, 'form']],
            }
        mrp_automation = self.create({'mo_error': True, 'mo_name': barcode})
        view_id = self.env.ref('mrp_wo_produce.mrp_automation_form').id
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
