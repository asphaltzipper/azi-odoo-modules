# -*- coding: utf-8 -*-

from odoo import fields, models


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    priority = fields.Selection(
        default="0",
        required=True)
