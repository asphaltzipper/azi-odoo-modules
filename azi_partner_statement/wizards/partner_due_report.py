from odoo import models, fields, api


class PartnerDueReport(models.TransientModel):
    _name = 'partner.due.report'
    _description = 'Partner Due Amount Report'

    def generate_partners(self):
        partners = self.env['res.partner'].search([('customer', '=', True), ('parent_id', '=', False)]).filtered(
            lambda p: p.total_due)
        return{
            'type': 'ir.actions.act_window',
            'name': 'AZ Outstanding Balance Report',
            'res_model': 'res.partner',
            'target': 'current',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'domain': [('id', 'in', partners.ids)],
        }
