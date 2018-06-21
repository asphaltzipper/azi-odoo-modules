# -*- coding: utf-8 -*-

from odoo import api, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

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
        diff = dict(show_address=None, show_address_only=None, show_email=None)
        diff['override_display_name'] = True
        names = dict(self.with_context(**diff).name_get())
        for partner in self:
            partner.display_name = names.get(partner.id)
