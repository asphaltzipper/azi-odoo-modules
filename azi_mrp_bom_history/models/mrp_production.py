from odoo import fields, models, api, Command


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.model_create_multi
    def create(self, vals_list):
        productions = super(MrpProduction, self).create(vals_list)
        for production in productions:
            if not production.bom_id:
                continue
            bom_lines = self.get_bom_lines(production.product_qty, production.bom_id.id)
            bom_history_lines = []
            for line in bom_lines:
                bom_history_lines.append((0, 0, {'sequence': line[0], 'product_id': line[1],
                                                 'parent_product_id': line[2], 'bom_id': line[3],
                                                 'product_qty': line[7], 'product_uom_id': line[8],
                                                 'bom_type': line[4]}))
            self.env['mrp.bom.history'].create({'mrp_production_id': production.id, 'bom_id': production.bom_id.id,
                                                'bom_history_line_ids': bom_history_lines})
        return productions

    def get_bom_lines(self, quantity, bom_id):
        lang = self.env.lang
        self._cr.execute("""
            with recursive bom_stack (parent_prod_id, comp_prod_id, level, name_path, bom_id, bom_line_id, bom_type, 
                                      qty, product_uom_id) as (
            select
                b.product_id as parent_id,
                l.product_id as comp_id,
                0 as level,
                coalesce(pp.default_code, t.name->> %s, '') as name_path,
                b.id as bom_id,
                l.id as line_id,
                b.type as bom_type,
                (l.product_qty * %s) as qty,
                l.product_uom_id as product_uom_id
            from mrp_bom_line as l
            left join mrp_bom as b on b.id=l.bom_id
            left join product_product as pp on pp.id=l.product_id
            left join product_template as t on t.id=pp.product_tmpl_id
            where bom_id= %s
            union select
                b.product_id as parent_id,
                l.product_id as comp_id,
                p.level + 1 as level,
                p.name_path || ' | ' || coalesce(pp.default_code, t.name ->> %s, '') as name_path,
                b.id as bom_id,
                l.id as line_id,
                b.type as bom_type,
                (p.qty * l.product_qty),
                l.product_uom_id as product_uom_id
            from mrp_bom_line as l
            left join (
                select distinct on (product_id)
                id,
                product_tmpl_id,
                product_id,
                type
                from mrp_bom
                where active=true
                order by product_id, sequence
            ) as b on b.id=l.bom_id
            left join product_product as pp on pp.id=l.product_id
            left join product_template as t on t.id=pp.product_tmpl_id
            inner join bom_stack as p on b.product_id=p.comp_prod_id
            )
            select
                level,
                comp_prod_id,
                parent_prod_id,
                bom_id,
                bom_type,
                bom_line_id,
                name_path,
                qty,
                t.product_uom_id
            from bom_stack as t
            left join mrp_bom as b on b.id = t.bom_id
            order by name_path
        """, (lang, quantity, bom_id, lang)
        )
        return self._cr.fetchall()
