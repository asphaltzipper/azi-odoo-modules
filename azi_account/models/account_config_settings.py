from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    apply_retail_taxes = fields.Boolean('Apply Retail Taxes')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(apply_retail_taxes=self.env['ir.config_parameter'].sudo().get_param(
                'azi_account.apply_retail_taxes', default=False))
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param(
            'azi_account.apply_retail_taxes', self.apply_retail_taxes)
