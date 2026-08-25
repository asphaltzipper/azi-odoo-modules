from odoo import models, fields, api


class AccountMailLog(models.Model):
    _name = 'account.mail.log'
    _description = 'Account Mail Log'

    log_type = fields.Selection([('info', 'Info'), ('error', 'Error')], 'Type', required=True)
    message = fields.Char('Message', required=True)
