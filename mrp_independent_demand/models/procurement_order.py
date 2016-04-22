# -*- coding: utf-8 -*-
# © 2016 Matt Taylor - Asphalt Zipper
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class ProcurementOrder(models.Model):
    _inherit = "procurement.order"

    def _prepare_mo_vals(self, context=None):
        self.ensure_one()
        res = super(ProcurementOrder, self)._prepare_mo_vals(procurement, context=context)
        res['date_planned_end'] = fields.Datetime.from_string(self.date_planned)
        return res
