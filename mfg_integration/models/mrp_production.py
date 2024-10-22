from odoo import api, fields, models


class MrpBom(models.Model):
    _inherit = 'mrp.production'

    routing_name = fields.Char(
        related="bom_id.routing_name",
        store=True,
    )
