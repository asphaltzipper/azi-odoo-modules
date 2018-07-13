# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class BomStructureReport(models.AbstractModel):
    _name = 'report.mrp.report_mrpbomstructure'

    def get_children(self, bom_id):
        children = []
        cr = self._cr
        cr.execute(
            """with recursive bom_tree (parent_prod_id, comp_prod_id, level, name_path, p_type_id, bom_id, line_id, bom_type, qty) as (
                    select
                        b.product_id as parent_id,
                        l.product_id as comp_id,
                        0 as level,
                        coalesce(pp.default_code, t.name, '') as name_path,
                        coalesce(b.picking_type_id, 0) as p_type_id,
                        b.id as bom_id,
                        l.id as line_id,
                        b.type as bom_type,
                        l.product_uom_qty / b.product_uom_qty as qty
                    from mrp_bom_line as l
                    left join mrp_bom as b on b.id=l.bom_id
                    left join product_product as pp on pp.id=l.product_id
                    left join product_template as t on t.id=pp.product_tmpl_id
                    where bom_id=%s
                union
                    select
                        b.product_id as parent_id,
                        l.product_id as comp_id,
                        p.level + 1 as level,
                        p.name_path | | ' | ' | | coalesce(pp.default_code, t.name, '') as name_path,
                        coalesce(b.picking_type_id, 0) as p_type_id,
                        b.id as bom_id,
                        l.id as line_id,
                        b.type as bom_type,
                        (p.qty * l.product_uom_qty) / b.product_uom_qty
                    from mrp_bom_line as l
                    left join (
                        -- the problem with getting default boms all at once is
                        -- we need to get the child bom based on the picking type of the parent bom
                        -- then sort by version and sequence and take the first record
                        select distinct on (product_id, coalesce(picking_type_id, 0))
                            id,
                            product_tmpl_id,
                            product_id,
                            coalesce(picking_type_id, 0) as picking_type_id,
                            type
                        from mrp_bom
                        where active=true
                        order by product_id, coalesce(picking_type_id, 0), version desc, sequence
                    ) as b on b.id=l.bom_id
                    left join product_product as pp on pp.id=l.product_id
                    left join product_template as t on t.id=pp.product_tmpl_id
                    inner join bom_tree as p on b.product_id=p.comp_prod_id and b.picking_type_id=p.p_type_id
            )
            select
                level,
                comp_prod_id,
                bom_id,
                bom_type,
                bom_line_id,
                b.code,
                qty
            from bom_tree as t
            left join mrp_bom as b on b.id=t.bom_id
            order by name_path""", bom_id,)
        data = cr.fetchall()
        prod_obj = self.env['product.product']
        line_obj = self.env['mrp.bom.line']
        for row in data:
            product = prod_obj.browse(row[1])
            bom_line = line_obj.browse(row[4])
            res = {}
            res['pname'] = product.display_name
            res['pid'] = row[0]
            res['pcode'] = product.default_code
            res['uname'] = bom_line.product_uom_id.name
            res['level'] = row[0]
            res['puom'] = bom_line.product_uom_id
            res['code'] = row[5]
            res['pqty'] = row[7]
            children.append(res)

        return children

    @api.multi
    def render_html(self, docids, data=None):
        docargs = {
            'doc_ids': docids,
            'doc_model': 'mrp.bom',
            'docs': self.env['mrp.bom'].browse(docids),
            'get_children': self.get_children,
            'data': data,
        }
        return self.env['report'].render('mrp.mrp_bom_structure_report', docargs)
