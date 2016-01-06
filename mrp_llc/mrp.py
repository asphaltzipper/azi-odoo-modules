# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP Module
#
#    Copyright (C) 2014 Asphalt Zipper, Inc.
#    Author scosist
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from openerp import api, fields, models


class mrp_bom_llc(models.Model):
    _name = "mrp.bom.llc"
    _description = "MRP Low Level Code"
    _auto = False
    _order = 'llc'

    llc = fields.Integer('Product LLC', readonly=True)

    _depends = {
        'mrp.bom': ['product_id', 'type'],
        'mrp.bom.line': ['product_id', 'bom_id'],
    }

    def init(self, cr):
        cr.execute("""create or replace view mrp_bom_llc as (
            -------------------------------------------------------------------
            -- in order to handle phantom assemblies, need to change 2 things
            --  1. only push to the path array when type is not phantom
            --  2. finally exclude phantom-only components from the list
            with recursive stack(parent_id, comp_id, path, comp_phantom) as (
                SELECT
                    bp.product_id,
                    l.product_id,
                CASE WHEN bp.type<>'phantom' AND COALESCE('', bc.type)<>'phantom' THEN
                    ARRAY[bp.product_id, l.product_id]
                    when bp.type<>'phantom' AND COALESCE('', bc.type)='phantom' THEN
                    ARRAY[bp.product_id]
                    when bp.type='phantom' AND COALESCE('', bc.type)<>'phantom' THEN
                    ARRAY[l.product_id]
                    ELSE
                    ARRAY[]::int[]
                    END,
                CASE WHEN bc.type='phantom' THEN true ELSE false END
                FROM mrp_bom AS bp, mrp_bom_line AS l
                LEFT JOIN mrp_bom AS bc ON bc.product_id=l.product_id
                WHERE bp.id=l.bom_id
                AND bp.product_id NOT IN (SELECT product_id FROM mrp_bom_line)
            UNION ALL
                SELECT
                    bp.product_id,
                    l.product_id,
                CASE WHEN bc.type<>'phantom' THEN
                    path || l.product_id
                    ELSE
                    path
                    END,
                    CASE WHEN bc.type='phantom' THEN true ELSE false END
                FROM stack AS s, mrp_bom AS bp, mrp_bom_line AS l
                LEFT JOIN mrp_bom AS bc ON bc.product_id=l.product_id
                WHERE bp.product_id=s.comp_id
                AND bp.id=l.bom_id
            )
            SELECT
                op.id,
                CASE WHEN BOOL_AND(comp_phantom) THEN 0 ELSE COALESCE(MAX(ARRAY_LENGTH(path, 1))-1, 0) END AS llc
            FROM stock_warehouse_orderpoint AS op
            LEFT JOIN stack AS s ON op.product_id=s.comp_id
            GROUP BY op.id
            -------------------------------------------------------------------
        )""")

    @api.model
    def update_orderpoint_llc(self):
        llc_obj = self.env['mrp.bom.llc']
        llc_ids = llc_obj.search([])
        for llc_id in llc_ids:
            for orderpoint in self.env['stock.warehouse.orderpoint'].search(
                    [('id', '=', llc_id.id)]):
                orderpoint.llc = llc_id.llc
