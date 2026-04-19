import json

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MQTTProcessMessage(models.TransientModel):
    _name = 'mqtt.process.message'
    _description = 'MQTT Process Message'

    payload = fields.Text()
    history_id = fields.Many2one('mqtt.message.history', 'History')

    @api.model
    def default_get(self, fields):
        res = super(MQTTProcessMessage, self).default_get(fields)
        history = self.env['mqtt.message.history'].browse(self._context['active_id'])
        res['history_id'] = history.id
        res['payload'] = history.payload
        return res

    def action_process(self):
        self.history_id.process_telemetry()
