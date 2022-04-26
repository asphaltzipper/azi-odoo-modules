from odoo import models, fields


class MaterialPlanLog(models.Model):
    _name = 'material.plan.log'
    _description = 'Plan Material Log'
    _order = 'create_date desc'

    type = fields.Selection(
        selection=[
            ('info', 'Info'),
            ('debug', 'Debug'),
            ('warning', 'Warning'),
            ('error', 'Error'),
        ],
        string='Type',
        required=True,
        readonly=True,
    )

    message = fields.Char(
        string='Message',
        required=True,
        readonly=True,
    )
