from odoo import models, api, fields


class MqttClient(models.Model):
    _name = 'mqtt.client'
    _description = 'MQTT Client'

    _sql_constraints = [('name_uniq', 'unique (name)', """Client name must be unique."""), ]

    name = fields.Char(
        string='Name',
        help="ICCID from the SIM card",
    )
    serial_ids = fields.One2many(
        comodel_name='mqtt.client.serial',
        inverse_name='client_id',
        string='Serial Numbers',
    )
    current_lot_id = fields.Many2one(
        comodel_name='stock.lot',
        compute='_compute_current_lot_id',
    )
    hologram_state = fields.Selection(
        selection=[
            ('live', 'LIVE'),
            ('live-pending', 'LIVE - PENDING'),
            ('pause-pending-user', 'PAUSE - PENDING - USER'),
            ('pause-pending-sys', 'PAUSE - PENDING - SYS'),
            ('paused-user', 'PAUSED - USER'),
            ('paused-sys', 'PAUSED - SYS'),
        ],
        string='Hologram State',
        required=True,
        default='live-pending',
    )
    history_ids = fields.One2many(
        comodel_name='mqtt.message.history',
        inverse_name='client_id',
        string='Signal History',
    )
    incoming_message_count = fields.Integer(
        string="Incoming Message Count",
        compute="_compute_message_count",
    )
    outgoing_message_count = fields.Integer(
        string="Outgoing Message Count",
        compute="_compute_message_count",
    )

    @api.depends('serial_ids', 'serial_ids.sequence')
    def _compute_current_lot_id(self):
        for rec in self:
            if rec.serial_ids:
                rec.current_lot_id = rec.serial_ids[0].lot_id
            else:
                rec.current_lot_id = False

    @api.depends('history_ids.direction', 'history_ids.client_id')
    def _compute_message_count(self):
        for rec in self:
            rec.outgoing_message_count = len([
                res for res in rec.history_ids if res.direction == 'outgoing'
            ])
            rec.incoming_message_count = len([
                res for res in rec.history_ids if res.direction == 'incoming'
            ])

    def action_review_incoming_history(self):
        self.ensure_one()
        action = self.env.ref('mqtt_integration.action_mqtt_incoming_message').read()[0]
        action.update({
            'domain': [
                ('client_id', '=', self.id),
                ('direction', '=', 'incoming'),
            ],
            'context': {
                'default_client_id': self.id,
                'default_direction': 'incoming'
            }
        })
        return action

    def action_review_outgoing_history(self):
        self.ensure_one()
        action = self.env.ref('mqtt_integration.action_mqtt_outgoing_message').read()[0]
        action.update({
            'domain': [
                ('client_id', '=', self.id),
                ('direction', '=', 'outgoing'),
            ],
            'context': {
                'default_client_id': self.id,
                'default_direction': 'outgoing'
            }
        })
        return action
