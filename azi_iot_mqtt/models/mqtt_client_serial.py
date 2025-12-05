from odoo import models, api, fields


class MqttClientSerial(models.Model):
    _name = 'mqtt.client.serial'
    _description = 'MQTT Client Serial'
    _order = 'sequence'

    name = fields.Char('Name')
    client_id = fields.Many2one(
        comodel_name='mqtt.client',
        string="Client",
        required=True,
    )
    lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Serial Number',
        required=True,
    )
    sequence = fields.Integer(
        string='Sequence',
        required=True,
        default=1,
    )
    install_date = fields.Date(
        string='Install Date',
        required=True,
        default=fields.Date.today(),
    )
