from odoo import models, fields, api


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    imported = fields.Boolean('Imported')
