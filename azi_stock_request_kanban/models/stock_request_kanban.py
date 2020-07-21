from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class StockRequestKanban(models.Model):
    _inherit = 'stock.request.kanban'

    state = fields.Selection([('draft', 'Draft'), ('submit', 'Submitted'), ('done', 'Done'), ('cancel', 'Cancelled')],
                             'Status', default='draft')

    @api.multi
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_('You can only delete stock request kanban in draft status'))

    @api.multi
    @api.depends('name', 'state')
    def name_get(self):
        return [(record.id, "%s/%s" % (record.name, record.state)) for record in self]

    def action_submit(self):
        self.state = 'submit'

    def action_done(self):
        self.state = 'done'

    def action_cancel(self):
        self.state = 'cancel'
