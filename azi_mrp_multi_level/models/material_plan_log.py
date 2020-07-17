from odoo import models, fields


class MaterialPlanLog(models.Model):
    _name = 'material.plan.log'
    _description = 'Plan Material Log'
    _order = 'create_date desc'

    type = fields.Selection([('info', 'Info'), ('debug', 'Debug'), ('warning', 'Warning')], 'Type', required=True,
                            readonly=True)
    message = fields.Char('Message', required=True, readonly=True)
