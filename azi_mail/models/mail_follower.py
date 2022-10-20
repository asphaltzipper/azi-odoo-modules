from odoo import models, api, _


class Followers(models.Model):
    _inherit = 'mail.followers'

    @api.model
    def remove_unneeded_followers(self):
        internal_partners = self.env['res.users'].search([('share', '=', False)]).mapped('partner_id.id')
        unneeded_followers = self.search([('partner_id', '!=', False),
                                          ('partner_id', 'not in', internal_partners)])
        unneeded_followers.unlink()
