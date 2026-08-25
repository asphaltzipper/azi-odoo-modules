from odoo import models, fields, api


class UnitTelemetryType(models.Model):
    _name = 'unit.telemetry.type'
    _description = 'Data type definition for telemetry readings'
    _sql_constraints = [(
        'name_topic_uniq',
        'unique (name, topic_id)',
        "The combination of JSON Key and Topic must be unique."
    )]

    name = fields.Char(
        string='JSON Key',
        copy=False,
    )
    topic_id = fields.Many2one(
        comodel_name='unit.telemetry.topic',
        string='Topic',
        required=True,
    )
    data_type = fields.Selection(
        selection=[
            ('char', 'String'),
            ('float', 'Float'),
            ('integer', 'Integer'),
            ('datetime', 'Datetime'),
            ('date', 'Date'),
            ('bool', 'Boolean'),
        ],
        required=True,
        default='char',
    )
    description = fields.Char(
        string='Description',
        required=True,
    )
    help = fields.Text(
        string='Explanation',
    )
