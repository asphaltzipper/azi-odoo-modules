from odoo import models, api, _
from odoo.exceptions import ValidationError


class MailWizardInvite(models.TransientModel):
    _inherit = 'mail.wizard.invite'

    @api.multi
    def add_followers(self):
        if self.partner_ids:
            raise ValidationError(_('Sorry, you are not allowed to add a follower'))
        return super(MailWizardInvite, self).add_followers()
