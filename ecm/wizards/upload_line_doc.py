# -*- coding: utf-8 -*-

import base64

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class EcmEcoRevLineDoc(models.TransientModel):
    _name = 'ecm.eco.rev.line.doc'
    _description = 'Upload ECO Revision Document'

    data_file = fields.Binary(
        string='ECO Product Revision Document',
        required=True)

    filename = fields.Char(
        string="Filename")

    line_id = fields.Many2one(
        comodel_name='ecm.eco.rev.line',
        string="ECO Revision Line",
        readonly=True,
        required=True,
        ondelete='cascade')

    @api.model
    def default_get(self, fields):
        res = super(EcmEcoRevLineDoc, self).default_get(fields)
        res['line_id'] = self._context['active_id']
        return res

    @api.multi
    def action_upload(self):
        """Upload attachment to ECO Line."""

        # Decode the file data
        data = base64.b64decode(self.data_file)
        self.line_id.attach_document(self.filename, data)
        return {}
