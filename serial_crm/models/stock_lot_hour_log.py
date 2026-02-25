from odoo import models, fields, api


class StockLotHourLog(models.Model):
    _name = 'stock.lot.hour.log'
    _description = 'Serialized Unit Hour Logs'
    _order = 'date desc'

    date = fields.Datetime(
        string='Date',
        required=True,
        default=fields.Datetime.now(),
    )
    lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Serial',
        required=True,
    )
    hours = fields.Float(string='Hours')
    hrs = fields.Char()
    note = fields.Char(string="Note")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'hours' in vals:
                vals['hrs'] = str(vals['hours'])
            elif 'hrs' in vals:
                vals['hours'] = float(vals['hrs'])
        super(StockLotHourLog, self).create(vals_list)

    def write(self, vals):
        if 'hours' in vals and 'hrs' not in vals:
            vals['hrs'] = str(vals['hours'])
        elif 'hrs' in vals and 'hours' not in vals:
            vals['hours'] = float(vals['hrs'])
        super(StockLotHourLog, self).write(vals)
