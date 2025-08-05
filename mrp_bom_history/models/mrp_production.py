from odoo import fields, models, api, Command


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    bom_history_line_ids = fields.One2many('mrp.bom.history.line', 'production_id', 'BOM History')
    bom_history_count = fields.Integer('BOM History Count')

    @api.model_create_multi
    def create(self, vals_list):
        productions = super(MrpProduction, self).create(vals_list)
        for production in productions:
            if not production.bom_id:
                continue
            bom_lines = self.get_bom_lines(production.bom_id.id)
            bom_history_lines = []
            for line in bom_lines:
                bom_history_lines.append((0, 0, {'product_id': line[3], 'parent_product_id': line[2], 'bom_id': line[0],
                                                 'product_qty': line[4], 'product_uom_id': line[5],
                                                 'bom_type': line[1]}))
            production.write({'bom_history_line_ids': bom_history_lines})
        return productions

    def get_bom_lines(self, bom_id):
        self._cr.execute("""
            with recursive bom_stack (
                bom_id,
                bom_type,
                parent_prod_id,
                comp_prod_id,
                qty,
                uom_id
            ) as (
                    select
                        b.id as bom_id,
                        b.type as bom_type,
                        b.product_id as parent_id,
                        l.product_id as comp_id,
                        l.product_qty as qty,
                        l.product_uom_id as uom_id
                    from mrp_bom_line as l
                    left join mrp_bom as b on b.id=l.bom_id
                    where bom_id=%s
                union
                    select
                        b.id as bom_id,
                        b.type as bom_type,
                        b.product_id as parent_id,
                        l.product_id as comp_id,
                        l.product_qty,
                        l.product_uom_id
                    from mrp_bom_line as l
                    left join (
                        -- get default bom for component
                        select distinct on (product_id)
                            id,
                            type,
                            product_id
                        from mrp_bom
                        where active=true
                        order by product_id, sequence
                    ) as b on b.id=l.bom_id
                    inner join bom_stack as p on b.product_id=p.comp_prod_id
            )
            select
                bom_id,
                bom_type,
                parent_prod_id,
                comp_prod_id,
                qty,
                uom_id
            from bom_stack as t
            left join mrp_bom as b on b.id = t.bom_id
        """, (bom_id,)
        )
        return self._cr.fetchall()

    def action_view_mrp_bom_history(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'BOM History',
            'res_model': 'mrp.production',
            'target': 'current',
            'view_mode': 'tree',
            'domain': [('production_id', '=', self.id)]
        }
