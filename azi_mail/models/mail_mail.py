from odoo import models, api, _


class Mail(models.Model):
    _inherit = 'mail.mail'

    @api.model
    def remove_failed_mails(self):
        internal_partners = self.env['res.users'].search([('share', '=', False)]).mapped('partner_id.id')
        unneeded_mails = self.sudo().search([('recipient_ids', '!=', False),
                                             ('recipient_ids', 'not in', internal_partners)])
        unneeded_mails.unlink()
