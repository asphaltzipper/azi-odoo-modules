# -*- coding: utf-8 -*-

from odoo import api, models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _order = 'priority desc, name'

    priority = fields.Selection(
        selection=[('0', 'Normal'),
                   ('1', 'Low'),
                   ('2', 'High'),
                   ('3', 'Very High')],
        string="Priority",
        default="0",
        required=True,
        help="Gives the sequence order when displaying a list of tasks.")

    state_code = fields.Char(
        string='State Code',
        help='The state code.',
        related='state_id.code',
        required=True)

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
                    if partner.name:
                        name = "[%s - %s] " % (partner.type.upper(), partner.name)
                    else:
                        name = "[%s] " % partner.type.upper()
                if not partner.is_company:
                    flat_address = partner._flat_address()
                    name = "%s, %s %s" % (
                        partner.commercial_company_name or partner.parent_id.name,
                        name,
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
