# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    code = fields.Char(string='Code', index=True)

    # set unique case sensitive constraint on the database field
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'A record with the same code already exists [code_unique]')
    ]

    # force uppercase for code field in view (res.partner.form)
    @api.onchange('code')
    def onchange_case(self):
        if self.code:
            self.code = self.code.replace(' ', '').upper()

    # force uppercase for code field on res_partner record create
    @api.model
    def create(self, default=None):
        if self.code:
            self.code.replace(' ', '').upper()
        return super(ResPartner, self).create(default)

    # force uppercase for code field on res_partner record write
    @api.model
    def write(self, default=None):
        if self.code:
            self.code.replace(' ', '').upper()
        return super(ResPartner, self).write(default)

    # on copy, append to the partner code to maintain uniqueness
    @api.model
    def copy(self, default=None):
        if not default:
            default = {}
        default = default.copy()
        default['code'] = self.code + _('(COPY)')
        return super(ResPartner, self).copy(default)
