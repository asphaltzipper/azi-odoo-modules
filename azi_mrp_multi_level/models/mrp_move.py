from odoo import models, fields


class MrpMove(models.Model):
    _inherit = 'mrp.move'

    request_id = fields.Many2one(
        comodel_name='stock.request',
        string='Stock Request',
    )
