from odoo import models, api, fields


class MqttClient(models.Model):
    _name = 'mqtt.client'
    _description = 'Client SIM'

    name = fields.Char('Name')
    lot_ids = fields.Many2many('stock.lot', sting='Serial Numbers')
    hour_log_ids = fields.One2many('mqtt.hour.log', 'mqtt_client_id', 'Hour Logs')


class MqttHourLog(models.Model):
    _name = 'mqtt.hour.log'

    date = fields.Date('Date')
    hour = fields.Float('Hour')
    mqtt_client_id = fields.Many2one('mqtt.client', 'Client')


class MqttTopic(models.Model):
    _inherit = 'mqtt.topic'

    mqtt_client_id = fields.Many2one('mqtt.client', 'Client')