# -*- coding: utf-8 -*-
# © 2016 Scott Saunders - Asphalt Zipper, Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class ProcurementOrder(models.Model):
    _inherit = "procurement.order"

    # override mrp/procurement
    def check_bom_exists(self, cr, uid, ids, context=None):
        """ Finds the bill of material for the product from procurement order.
        @return: True or False
        """
        for procurement in self.browse(cr, uid, ids, context=context):
            ctx = context and context.copy() or {}
            ctx['bom_effectivity_date'] = self._get_date_planned(cr, uid, procurement, context=context).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            properties = [x.id for x in procurement.property_ids]
            bom_id = self.pool.get('mrp.bom')._bom_find(cr, uid, product_id=procurement.product_id.id,
                                                        properties=properties, context=ctx)
            if not bom_id:
                return False
        return True

    # override mrp/procurement
    def _prepare_mo_vals(self, cr, uid, procurement, context=None):
        res_id = procurement.move_dest_id and procurement.move_dest_id.id or False
        newdate = self._get_date_planned(cr, uid, procurement, context=context)
        bom_obj = self.pool.get('mrp.bom')
        if procurement.bom_id:
            bom_id = procurement.bom_id.id
            routing_id = procurement.bom_id.routing_id.id
        else:
            ctx = context and context.copy() or {}
            ctx['bom_effectivity_date'] = newdate.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            ctx['company_id'] = procurement.company_id.id
            properties = [x.id for x in procurement.property_ids]
            bom_id = bom_obj._bom_find(cr, uid, product_id=procurement.product_id.id,
                                       properties=properties, context=ctx)
            bom = bom_obj.browse(cr, uid, bom_id, context=context)
            routing_id = bom.routing_id.id
        return {
            'origin': procurement.origin,
            'product_id': procurement.product_id.id,
            'product_qty': procurement.product_qty,
            'product_uom': procurement.product_uom.id,
            'location_src_id': procurement.rule_id.location_src_id.id or procurement.location_id.id,
            'location_dest_id': procurement.location_id.id,
            'bom_id': bom_id,
            'routing_id': routing_id,
            'date_planned': newdate.strftime('%Y-%m-%d %H:%M:%S'),
            'move_prod_id': res_id,
            'company_id': procurement.company_id.id,
        }
