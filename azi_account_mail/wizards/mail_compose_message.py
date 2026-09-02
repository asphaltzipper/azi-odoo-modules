from odoo import models, api


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.onchange('template_id')
    def _onchange_template_id_wrapper(self):
        super(MailComposeMessage, self)._onchange_template_id_wrapper()
        partner_ids = self._context.get('default_partner_ids')
        if partner_ids:
            setattr(self, 'partner_ids', [[6, 0, partner_ids]])
