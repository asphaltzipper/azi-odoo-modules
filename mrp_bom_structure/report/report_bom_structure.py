from odoo import api, models


class ReportMrpBomStructureDown(models.AbstractModel):
    _name = "report.mrp_bom_structure.bom_structure_down"
    _description = "Downward BOM Structure Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('mrp_bom_structure.bom_structure_down')

        sql = """
            with recursive bom_tree (parent_prod_id, comp_prod_id, level, qty, name_path, p_type_id) as (
                    select
                        b.product_id as parent_id,
                        l.product_id as comp_id,
                        0 as level,
                        l.product_qty as qty,
                        coalesce(pp.default_code, t.name->>'en_US', '') as name_path,
                        coalesce(b.picking_type_id, 0) as p_type_id
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
                        l.product_qty as qty,
                        p.name_path || ' | ' || coalesce(pp.default_code, t.name->>'en_US', '') as name_path,
                        coalesce(b.picking_type_id, 0) as p_type_id
                    from mrp_bom_line as l
                    left join (
                        -- get the child bom based on the picking type of the parent bom
                        -- then sort by version and sequence and take the first record
                        select distinct on (product_id, coalesce(picking_type_id,0))
                            id,
                            product_tmpl_id,
                            product_id,
                            coalesce(picking_type_id,0) as picking_type_id,
                            type,
                            config_ok
                        from mrp_bom
                        where active=true
                        order by product_id, coalesce(picking_type_id,0), version desc, sequence
                    ) as b on b.id=l.bom_id
                    left join product_product as pp on pp.id=l.product_id
                    left join product_template as t on t.id=pp.product_tmpl_id
                    inner join bom_tree as p on b.product_id=p.comp_prod_id and b.picking_type_id=p.p_type_id
            )
            select
                t.level,
                t.comp_prod_id as product_id,
                (case when pp.default_code is not null then '[' || pp.default_code || '] ' else '' end) || (pt.name->>'en_US') as display_name,
                t.qty,
                uu.name->>'en_US' as uom_name,
                t.name_path
            from bom_tree as t
            left join product_product pp on pp.id=t.comp_prod_id
            left join product_template pt on pt.id=pp.product_tmpl_id
            left join uom_uom uu on uu.id=pt.uom_id
            left join uom_category uc on uc.id=uu.category_id
            order by name_path
        """
        self.env.cr.execute(sql, (docids[0],))
        bom_data = [{
                'level': x[0],
                'product_id': x[1],
                'display_name': x[2],
                'qty': x[3],
                'uom_name': x[4],
                'name_path': x[5],
            } for x in self.env.cr.fetchall()]

        docs = {
            'lines': bom_data,
        }

        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docs,
        }
        return docargs
