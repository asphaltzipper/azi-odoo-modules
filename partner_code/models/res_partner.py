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
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'code' in vals and vals['code']:
                vals['code'] = vals['code'].replace(' ', '').upper()
        return super(ResPartner, self).create(vals_list)

    # force uppercase for code field on res_partner record write
    def write(self, vals):
        if vals.get('code'):
            vals['code'] = vals['code'].replace(' ', '').upper()
        return super(ResPartner, self).write(vals)

    # on copy, append to the partner code to maintain uniqueness
    def copy(self, default=None):
        if not default:
            default = {}
        default = default.copy()
        default['code'] = self.code + _('(COPY)')
        return super(ResPartner, self).copy(default)
