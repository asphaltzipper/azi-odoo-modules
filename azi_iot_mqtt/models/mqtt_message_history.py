from odoo import models, fields, api


class MQTTMessageHistory(models.Model):
    _inherit = 'mqtt.message.history'

    client_id = fields.Many2one(
        comodel_name='mqtt.client',
        string="Client",
    )
