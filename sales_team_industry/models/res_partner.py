# -*- coding: utf-8 -*-
# Copyright 2014-2016 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class Partner(models.Model):
    _inherit = 'res.partner'

    industry_id = fields.Many2one('res.partner.industry', 'Industry')

    @api.multi
    @api.constrains('industry_id', 'customer')
    def _require_industry(self):
        industry_required = 0
        settings_record = self.env['sale.config.settings'].search([])
        if settings_record:
            industry_required = settings_record[0].require_industry
        if not industry_required:
            return
        for record in self:
            if record.customer and not record.industry_id:
                raise ValidationError(_("Customers require a valid Industry."
                                        " (%s)") % record.industry_id)
