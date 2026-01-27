from odoo import models, fields, api, _


class StockLot(models.Model):
    _name = 'stock.lot'
    _inherit = ['stock.lot', 'portal.mixin']

    def _compute_access_url(self):
        super()._compute_access_url()
        for lot in self:
            lot.access_url = f'/my/serials/{lot.id}'
