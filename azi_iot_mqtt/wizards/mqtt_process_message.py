import json

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MQTTProcessMessage(models.TransientModel):
    _name = 'mqtt.process.message'

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
        client = self.history_id.client_id
        topic = self.history_id.subscription_id.topic_id
        if client and topic.dest_model_name:
            serial = client.serial_ids[0]
            if serial:
                payload_json = json.loads(self.payload)
                payload_json['lot_id'] = serial.lot_id.id
                payload_json['date'] = fields.Date.today()
                dest_model_fields = self.env[topic.dest_model_name]._fields.keys()
                invalid_payload_fields = [key for key in payload_json.keys() if key not in dest_model_fields]
                if invalid_payload_fields:
                    raise ValidationError(f'Those fields {invalid_payload_fields} don\'t exist '
                                          f'in this model {topic.dest_model_name}')
                else:
                    self.env[topic.dest_model_name].create(payload_json)
                    self.history_id.processed = True
                    self.history_id.payload = self.payload
