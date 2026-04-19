from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json
import logging
from datetime import date, datetime

_logger = logging.getLogger(__name__)


def try_parse_date(date_string, formats):
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    return None


class MQTTMessageHistory(models.Model):
    _inherit = 'mqtt.message.history'

    client_id = fields.Many2one(
        comodel_name='mqtt.client',
        string="Client",
    )
    processed = fields.Boolean(
        string='Processed',
        required=True,
        default=False,
        index=True,
    )
    topic_name = fields.Char(string='Topic Name')

    @api.model
    def process_telemetry(self, silent=False):
        tel_types = {x.name: x for x in self.env['unit.telemetry.type'].search([])}
        for msg in self:
            payload = {}
            try:
                payload = json.loads(msg.payload)
            except ValueError:
                error_message = _("Message '%s' has invalid payload: %s", msg.name, msg.payload)
                if silent:
                    _logger.error(error_message)
                    continue
                else:
                    raise ValidationError(error_message)

            timestamp_orig = payload.pop('time', '')
            timestamp = None
            if not timestamp_orig:
                _logger.error(_('Message %s has no timestamp in payload', msg.name))
            else:
                timestamp_dt = try_parse_date(timestamp_orig, ["%m/%d/%Y,%H:%M:%S", "%Y-%m-%d %H:%M:%S"])
                if timestamp_dt:
                    timestamp = timestamp_dt.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    _logger.error(_('Message has invalid timestamp %s', timestamp_orig))

            invalid_payload_fields = [key for key in payload.keys() if key not in tel_types.keys()]
            if invalid_payload_fields:
                error = _('Received fields not defined in telemetry: %s', invalid_payload_fields)
                if silent:
                    _logger.error(error)
                    continue
                else:
                    raise ValidationError(error)

            lot_id = msg.client_id.current_lot_id.id
            for key, val in payload.items():
                tel_type = tel_types[key]
                if not tel_type:
                    continue
                create_vals = {
                    'msg_id': msg.id,
                    'lot_id': lot_id,
                    'type_id': tel_type.id,
                    'char_value': val,
                }
                if timestamp:
                    create_vals['read_time'] = timestamp
                self.env['unit.telemetry.reading'].create(create_vals)
            msg.processed = True

    @api.model
    def cron_process_telemetry(self):
        msg_domain = [('client_id', '!=', False), ('processed', '=', False)]
        msgs = self.search(msg_domain)
        if msgs:
            msgs.process_telemetry(silent=True)
