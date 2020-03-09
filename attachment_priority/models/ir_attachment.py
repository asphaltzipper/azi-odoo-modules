from odoo import fields, models


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    priority = fields.Selection(
        selection=[
            ('0', 'Very Low'),
            ('1', 'Low'),
            ('2', 'Normal'),
            ('3', 'High'),
        ],
        default="0",
        required=True)
