from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    hologram_api_key = fields.Char(
        string='Hologram API Key',
        config_parameter='hologram.api_key',
        help='API Key for accessing Hologram.io REST API'
    )
    hologram_org_id = fields.Char(
        string='Hologram Organization ID',
        config_parameter='hologram.org_id',
        help='Your Hologram Organization ID'
    )
    hologram_plan = fields.Char(
        string='Hologram Default Plan',
        config_parameter='hologram.default_plan',
        help='Default plan for Hologram SIMs'
    )
