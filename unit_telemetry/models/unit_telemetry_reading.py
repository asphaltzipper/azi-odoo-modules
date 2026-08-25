from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date, datetime


def str_to_bool(value: str) -> bool:
    # Example: str_to_bool("True") -> True
    normalized = value.lower().strip()
    if normalized in ('true', '1', 't', 'y', 'yes'):
        return True
    elif normalized in ('false', '0', 'f', 'n', 'no'):
        return False
    else:
        raise ValueError(f"Cannot convert '{value}' to boolean.")

def str_to_float(value: str) -> float:
    # Example: str_to_float("3.14") -> 3.14
    try:
        new_val = float(value or 0)
    except ValueError as e:
        raise ValueError(_("Cannot convert '%s' to float: %s", value, e))
    return new_val

def str_to_int(value: str) -> int:
    # Example: str_to_int("42") -> 42
    try:
        new_val = int(value or 0)
    except ValueError as e:
        raise ValueError(_("Cannot convert '%s' to integer: %s", value, e))
    return new_val

# def str_to_date(value: str) -> date:
#     # Example: str_to_date("2026-04-14") -> datetime.date(2026, 4, 14)
#     return date.fromisoformat(value)
#
# def str_to_datetime(value: str) -> datetime:
#     # Handles format: "YYYY-MM-DD HH:MM:SS"
#     # Example: str_to_datetime("2026-04-14 18:36:00") -> datetime.datetime(2026, 4, 14, 18, 36)
#     return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


class UnitTelemetryReading(models.Model):
    _name = 'unit.telemetry.reading'
    _description = 'Serialized Unit Telemetry Reading'
    _order = 'read_time desc'

    msg_id = fields.Many2one(
        comodel_name='mqtt.message.history',
        string='Message Id',
        required=True,
    )
    read_time = fields.Datetime(
        string='Date',
        required=True,
        default=fields.Datetime.now(),
    )
    lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Serial',
        required=True,
    )
    type_id = fields.Many2one(
        comodel_name='unit.telemetry.type',
        required=True,
    )
    data_type = fields.Selection(
        related='type_id.data_type',
    )
    topic_id = fields.Many2one(
        related='type_id.topic_id',
        store=True,
        string='Topic',
    )
    char_value = fields.Char()
    float_value = fields.Float()
    integer_value = fields.Integer()
    date_value = fields.Date()
    datetime_value = fields.Datetime()
    bool_value = fields.Boolean()
    value = fields.Char(
        string='Computed Value',
        compute='_compute_value',
        store=True,
    )

    @api.depends('data_type', 'char_value', 'float_value', 'integer_value',
                 'date_value', 'datetime_value', 'bool_value')
    def _compute_value(self):
        field_map = {
            'char': 'char_value',
            'float': 'float_value',
            'integer': 'integer_value',
            'date': 'date_value',
            'datetime': 'datetime_value',
            'bool': 'bool_value',
        }
        for rec in self:
            rec.value = str(rec[field_map.get(rec['data_type'])])

    @api.constrains('data_type', 'char_value', 'float_value', 'integer_value',
                    'date_value', 'datetime_value', 'bool_value')
    def _check_required_field_by_type(self):
        # Map selection to field names
        field_map = {
            'char': 'char_value',
            'float': 'float_value',
            'integer': 'integer_value',
            'date': 'date_value',
            'datetime': 'datetime_value',
            'bool': 'bool_value',
        }

        for record in self:
            selected_type = record.data_type
            if not selected_type:
                continue

            field_name = field_map.get(selected_type)
            val = record[field_name]

            # Validation logic:
            # Check for empty state.
            # Note: For Boolean, we accept 'False' as a valid value if
            # the intention is to allow an unchecked state.
            is_invalid = False
            if selected_type == 'bool':
                # Booleans are inherently set, so they are rarely 'empty'
                is_invalid = False
            elif selected_type in ['float', 'integer']:
                # 0 is allowed, False/None is invalid
                is_invalid = (val is False or val is None)
            else:
                # Standard check for Char, Date, Datetime
                is_invalid = not val

            if is_invalid:
                raise ValidationError(_(
                    "Data type '%s' requires a value for '%s': '%s' is invalid.",
                    record._fields[selected_type].selection[0][1],
                    record._fields[field_name].string,
                    str(val),
                ))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not 'char_value' in vals:
                continue
            val_type = self.env['unit.telemetry.type'].browse(vals.get('type_id'))
            if val_type.data_type == 'char':
                continue
            if val_type.data_type == 'float':
                vals['float_value'] = str_to_float(vals['char_value'])
            elif val_type.data_type == 'integer':
                vals['integer_value'] = str_to_int(vals['char_value'])
            elif val_type.data_type == 'bool':
                vals['bool_value'] = str_to_bool(vals['char_value'])
            elif val_type.data_type == 'date':
                vals['date_value'] = vals['char_value']
            elif val_type.data_type == 'datetime':
                vals['datetime_value'] = vals['char_value']
        return super(UnitTelemetryReading, self).create(vals_list)

    def write(self, vals):
        val_type = (
            vals.get('type_id')
            and self.env['unit.telemetry.type'].browse(vals['type_id'])
            or self.type_id
        )
        if not 'char_value' in vals or val_type.data_type == 'char':
            return super(UnitTelemetryReading, self).write(vals)
        if val_type.data_type == 'float':
            vals['float_value'] = str_to_float(vals['char_value'])
        elif val_type.data_type == 'integer':
            vals['integer_value'] = str_to_int(vals['char_value'])
        elif val_type.data_type == 'bool':
            vals['bool_value'] = str_to_bool(vals['char_value'])
        elif val_type.data_type == 'date':
            vals['date_value'] = vals['char_value']
        elif val_type.data_type == 'datetime':
            vals['datetime_value'] = vals['char_value']
        return super(UnitTelemetryReading, self).write(vals)
