# -*- coding: utf-8 -*-
# See __openerp__.py file for full copyright and licensing details.

from odoo import api, fields, models


class MrpBomLlc(models.Model):
    _name = "mrp.bom.llc"
    _description = "MRP Low Level Code"
    _auto = False

    llc = fields.Integer('Orderpoint LLC', readonly=True)

    _depends = {
        'mrp.bom': ['product_id', 'type'],
        'mrp.bom.line': ['product_id', 'bom_id'],
    }

    @api.model_cr
    def init(self):
        cr = self._cr
        cr.execute("""create or replace view mrp_bom_llc as (
            with j as (
                -- if only template specified on mrp.bom, then expand list with all variants
                SELECT DISTINCT
                    COALESCE(b.product_id,p.id) AS parent_id,
                    l.product_id AS comp_id
                FROM mrp_bom_line AS l, mrp_bom AS b, product_product AS p
                WHERE b.product_tmpl_id=p.product_tmpl_id
                AND l.bom_id=b.id
            )
            SELECT *
            FROM (
                 -- build a path array
                with recursive stack(parent_id, comp_id, path) as (
                    SELECT
                        j.parent_id,
                        j.comp_id,
                        ARRAY[j.comp_id]
                    FROM j
                    WHERE j.parent_id NOT IN (SELECT comp_id FROM j)
                    UNION ALL
                    SELECT
                        j.parent_id,
                        j.comp_id,
                        path || j.comp_id
                    FROM stack AS s, j
                    WHERE j.parent_id=s.comp_id
                )
                -- use longest path for each orderpoint as llc
                SELECT
                    op.id,
                    COALESCE(MAX(ARRAY_LENGTH(path, 1)), 0) AS llc
                FROM stock_warehouse_orderpoint AS op
                LEFT JOIN stack AS s ON op.product_id=s.comp_id
                GROUP BY op.id
            ) AS res
        )""")

    @api.model
    def update_orderpoint_llc(self):
        for llc in self.search([]):
            for op in self.env['stock.warehouse.orderpoint'].browse(llc.id):
                op.llc = llc.llc

    def bom_loop_check(self):
        self._cr.execute("""
            with recursive j as (
                -- if only template specified on mrp.bom, then expand list with all variants
                SELECT DISTINCT
                    COALESCE(b.product_id,p.id) AS parent_id,
                    l.product_id AS comp_id
                FROM mrp_bom_line AS l, mrp_bom AS b, product_product AS p
                WHERE b.product_tmpl_id=p.product_tmpl_id
                AND l.bom_id=b.id
            ),
            stack(parent_id, comp_id, path, looped) as (
                SELECT
                    j.parent_id,
                    j.comp_id,
                    ARRAY[j.comp_id],
                    false
                FROM j
                WHERE j.parent_id NOT IN (SELECT comp_id FROM j)
                UNION ALL
                SELECT
                    j.parent_id,
                    j.comp_id,
                    path || j.comp_id,
                    j.comp_id = ANY(path)
                FROM stack AS s, j
                WHERE j.parent_id=s.comp_id
                AND NOT looped
            )
            select
                s.parent_id,
                s.comp_id,
                s.path
            from stack as s
            where looped
        """)

        # the array of component product ids for a given loop will always end with the re-encountered product
        # get a unique list of loops
        prod_obj = self.env['product.product']
        loops = []
        for data in self._cr.fetchall():
            loop_strings = []
            comp_id = data[1]
            index_start = data[2].index(comp_id)
            for prod_id in data[2][index_start:]:
                loop_strings.append(prod_obj.browse(prod_id).display_name)
            new_string = " ==>> ".join(loop_strings)
            if new_string not in loops:
                loops.append(new_string)
        return loops
