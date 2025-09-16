from odoo import fields, models


class ResPartnerIndustry(models.Model):
    _inherit = "res.partner.industry"

    credit_app = fields.Boolean(
        string='Require Credit App',
        required=True,
        default=True,
    )
