from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    portal_publish = fields.Boolean("Published to Portal", default=True, )

    def action_toggle_portal_publish(self):
        self.portal_publish = not self.portal_publish
