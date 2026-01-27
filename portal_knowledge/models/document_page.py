from odoo import models, fields, api, _


class DocumentPage(models.Model):
    _name = 'document.page'
    _inherit = ['document.page', 'portal.mixin']

    def _compute_access_url(self):
        super()._compute_access_url()
        for document in self:
            document.access_url = f'/my/knowledge/{document.id}'
