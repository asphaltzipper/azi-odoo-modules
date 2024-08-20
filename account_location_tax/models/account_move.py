from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    state_id = fields.Many2one('res.country.state', 'State', related='partner_id.state_id')
    zip = fields.Char(related='partner_id.zip')
    city = fields.Char(related='partner_id.city')
    state = fields.Selection(related='move_id.state')
    amount_untaxed = fields.Monetary('Untaxed Amount', related='move_id.amount_untaxed')
    amount_total = fields.Monetary('Total Amount', related='move_id.amount_total')
