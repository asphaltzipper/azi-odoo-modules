# -*- coding: utf-8 -*-
# © 2016 Matt Taylor - Asphalt Zipper
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, models, fields, _


class ProcurementOrder(models.Model):
    _inherit = "procurement.order"

    @api.model
    def _prepare_mo_vals(self, procurement):
        res = super(ProcurementOrder, self)._prepare_mo_vals(procurement)
        res['date_planned_end'] = fields.Datetime.from_string(procurement.date_planned)
        return res
