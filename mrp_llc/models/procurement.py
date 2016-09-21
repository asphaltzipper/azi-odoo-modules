# -*- coding: utf-8 -*-
# See __openerp__.py file for full copyright and licensing details.

from odoo import models, api


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    @api.model
    def _procurement_from_orderpoint_get_grouping_key(self, orderpoint_ids):
        res = super(ProcurementOrder, self)._procurement_from_orderpoint_get_grouping_key()
        orderpoints = self.env['stock.warehouse.orderpoint'].browse(orderpoint_ids)
        return res, orderpoints.llc

    @api.model
    def _procurement_from_orderpoint_get_order(self):
        res = super(ProcurementOrder, self)._procurement_from_orderpoint_get_order()
        self.env['mrp.bom.llc'].update_orderpoint_llc()
        return res + ',llc'
