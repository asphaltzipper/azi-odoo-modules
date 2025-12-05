from odoo import models, fields, api


class StockLotHourLog(models.Model):
    _name = 'stock.lot.hour.log'
    _description = 'Serialized Unit Hour Logs'

    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.today(),
    )
    lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Serial',
        required=True,
    )
    hours = fields.Float(string='Hours')
    hrs = fields.Char(
        compute='_compute_hrs',
        inverse='_inverse_hrs',
        readonly=True,
    )
    note = fields.Char(string="Note")

    def _inverse_hrs(self):
        for rec in self:
            try:
                rec.hours = int(rec.hrs)
            except:
                pass


    def _compute_hrs(self):
        for rec in self:
            rec.hrs = str(rec.hours)
