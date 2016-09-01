# -*- coding: utf-8 -*-
# See __openerp__.py file for full copyright and licensing details.

from openerp import models, api


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    @api.model
    def _update_llc(self):
        llc_obj = self.env['mrp.bom.llc']
        llc_obj.update_orderpoint_llc()

    @api.model
    def _procurement_from_orderpoint_get_order(self):
        self._update_llc()
        res = super(ProcurementOrder, self)._procurement_from_orderpoint_get_order()
        return res + ',llc'
