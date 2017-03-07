# -*- coding: utf-8 -*-
# Copyright 2014-2017 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class Partner(models.Model):
    _inherit = 'res.partner'

    industry_id = fields.Many2one('res.partner.industry', 'Industry')

    @api.multi
    def write(self, vals):
        if (self.env['ir.values'].get_default(
            'sale.config.settings', 'require_industry') and not (
                vals.get('parent_id') or self.parent_id and 'parent_id' not in
                vals)):
            if ((vals.get('customer') and not vals.get('industry_id')) or
                (self.customer and 'customer' not in vals and not
                 self.industry_id and 'industry_id' not in vals)):
                raise ValidationError(_("Customers require a valid Industry."))
        return super(Partner, self).write(vals)

    @api.model
    def create(self, vals):
        if (self.env['ir.values'].get_default(
            'sale.config.settings', 'require_industry') and not
                vals.get('parent_id')):
            if vals.get('customer') and not vals.get('industry_id'):
                raise ValidationError(_("Customers require a valid Industry."))
        return super(Partner, self).create(vals)
