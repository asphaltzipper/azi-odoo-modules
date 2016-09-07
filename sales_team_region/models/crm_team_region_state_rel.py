# -*- coding: utf-8 -*-
# Copyright 2014-2016 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import ValidationError
from openerp.tools.translate import _


class CrmTeamRegionStateRel(models.Model):
    _name = 'crm.team.region.state.rel'

    region_id = fields.Many2one('crm.team.region', 'Sales Region',
                                required=True, ondelete='cascade')
    state_id = fields.Many2one('res.country.state', 'State', required=True)

    #_sql_constraints = [
    #    ('rel_state_uniq', 'unique(state_id)',
    #     _('A region with the same state already exists [rel_state_uniq]')),
    #]
    @api.model
    @api.constrains('state_id')
    def _require_state_uniq(self):
        import pdb
        pdb.set_trace()
        for record in self:
            # if record.customer and not unique(record.state_id):
            self.region_types = record.region_id.region_types
            if record.state_id not in record.region_id._region_domain(1):
                raise ValidationError(_("A region with the same state (%s)"
                                        " already exists [_require_state_uniq]"
                                        ) % record.state_id)
    #@api.model
    #@api.constrains('partner_industry', 'customer')
    #def _require_team(self):
    #    for record in self:
    #        if record.customer and not record.partner_industry:
    #            raise ValidationError(_("Customers require a valid Industry."
    #                                    " (%s)") % record.partner_industry)
