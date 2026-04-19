from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockLot(models.Model):
    _inherit = 'stock.lot'

    telemetry_ids = fields.One2many(
         comodel_name='unit.telemetry.reading',
         inverse_name='lot_id',
         string='Telemetry Readings',
    )
    latest_telemetry = fields.Datetime(
        string="Latest Telemetry",
        compute='_compute_latest_telemetry',
    )

    @api.depends('telemetry_ids')
    def _compute_latest_telemetry(self):
        for lot in self:
            latest = (lot.telemetry_ids[:1] or [False])[0]
            lot.latest_telemetry = latest and latest.create_date or False

    def action_open_telemetry(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Telemetry Readings'),
            'res_model': 'unit.telemetry.reading',
            'view_mode': 'tree,form',
            'domain': [('lot_id', '=', self.id)],
            'context': {'default_lot_id': self.id},
        }
