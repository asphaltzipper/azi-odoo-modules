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

    @api.multi
    def _flat_address(self):
        address_format = "%(street)s, %(city)s, %(state_code)s"
        args = {
            'street': self.street or '',
            'city': self.city or '',
            'state_code': self.state_id.code or '',
        }
        return address_format % args

    @api.multi
    def name_get(self):
        if not self._context.get('override_display_name'):
            res = super(ResPartner, self).name_get()
            return res
        res = []
        for partner in self:
            name = partner.name or ''
            if partner.company_name or partner.parent_id:
                if partner.type in ['invoice', 'delivery', 'other']:
                    name = "[%s] " % partner.type
                if not partner.is_company:
                    flat_address = partner._flat_address()
                    name = "%s, %s %s" % (
                        partner.commercial_company_name or partner.parent_id.name,
                        name.upper(),
                        flat_address)
            name = name.replace('\n', ', ')
            res.append((partner.id, name))
        return res

    @api.depends('is_company', 'name', 'parent_id.name', 'type', 'company_name')
    def _compute_display_name(self):
        ctx = dict(self._context)
        ctx['override_display_name'] = True
        super(ResPartner, self).with_context(ctx)._compute_display_name()

