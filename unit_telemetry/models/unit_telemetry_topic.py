from odoo import models, fields, api


class UnitTelemetryTopic(models.Model):
    _name = 'unit.telemetry.topic'
    _description = 'Telemetry topic/category'
    _sql_constraints = [('name_uniq', 'unique(name)', "Topic Key must be unique.")]

    name = fields.Char(
        string='Topic Key',
        required=True,
        copy=False,
    )
    description = fields.Char(
        string='Description',
    )
    type_ids = fields.One2many(
        comodel_name='unit.telemetry.type',
        inverse_name='topic_id',
    )
