from odoo import models, api


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def register_as_main_attachment(self, force=True):
        if self.res_model == 'account.move':
            latest = self.search([
                ('res_model', '=', 'account.move'),
                ('res_id', '=', self.res_id),
            ], order='id desc', limit=1)
            record = self.env['account.move'].browse(self.res_id)
            if record.exists() and hasattr(record, 'message_main_attachment_id'):
                record.sudo().write({
                    'message_main_attachment_id': latest.id
                })
        return super(IrAttachment, self).register_as_main_attachment(force=force)

