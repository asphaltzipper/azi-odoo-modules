from odoo import models, api, fields


class MqttTopic(models.Model):
    _inherit = 'mqtt.topic'

    client_regex = fields.Char(
        string='Client RegEx',
        help="Regular Expression for extracting client ICCID from topic",
    )

    dest_model_name = fields.Selection(
        selection=[
            ('stock.lot.hour.log', 'Hours Log'),
            ('stock.lot.dtc.log', 'DTC Log'),
            ('stock.lot.gps.log', 'GPS Log'),
        ],
        string='Dest Model',
        help="The Odoo model in which to store the parsed payload data",
    )
