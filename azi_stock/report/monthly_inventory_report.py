from odoo import api, fields, models, tools


class MonthlyInventoryReport(models.Model):
    _name = 'monthly.inventory.report'
    _description = 'Monthly Builds Report'
    _auto = False

    serial = fields.Char('Serial')
    partnum = fields.Char('Part Number')
    model = fields.Char('Model')
    category = fields.Char('Category')
    build_date = fields.Date('Build Date')
    reference = fields.Char('Reference')
    curr_loc = fields.Char('Current Location')
    customer = fields.Char('Customer')
    orig_build = fields.Boolean('Origin Build')
    wa_unit = fields.Integer('WA Unit')

    def init(self):
        tools.drop_view_if_exists(self._cr, 'monthly_inventory_report')
        self._cr.execute("""
            CREATE VIEW monthly_inventory_report AS (
                select
                --im.lot_id,
                spl.id,
                spl.name as serial,
                pp.default_code as partnum,
                pt.name as model,
                pc.name as category,
                im.build_date,
                im.reference,
                sl.name as curr_loc,
                coalesce(prp.name, rp.name) as customer,
                case 
                    when fsm.sml_id=im.sml_id then true else false 
                end as orig_build, 
                case 
                    when wa.product_product_id is not null then 1 else 0 
                end as wa_unit
            from (
                -- inbound move 
                select
                    sml.id as sml_id,
                    sml.lot_id,
                    sml.product_id, sml.date::date as build_date, sml.reference
                from stock_move_line sml
                left join product_product pp on pp.id=sml.product_id
                left join product_template pt on pt.id=pp.product_tmpl_id left join product_category pc on pc.id=pt.categ_id
                where sml.lot_id is not null
                and pt.categ_id in (
                    select id
                    from product_category pc where pc.name like 'FG - %' and pc.name not in (
                    'FG - Grind Box',
                    'FG - Water System',
                    'FG - Shift Tilt',
                    'FG - CS Non Production'
                    ) 
                )
                and sml.location_id=(select id from stock_location where name='Production')
                and sml.location_dest_id=(select id from stock_location where name='Stock')
                and (pt.name ->> 'en_US') not ilike '%generic%'
            ) as im
            left join stock_lot spl on spl.id=im.lot_id
            left join product_product pp on pp.id=spl.product_id
            left join product_template pt on pt.id=pp.product_tmpl_id left join product_category pc on pc.id=pt.categ_id
            left join (
                -- last move (probably outbound, but not necessarily) 
                select distinct on (lot_id)
                    sml.lot_id,
                    sm.date, sm.location_dest_id
                from stock_move_line sml
                left join stock_move sm on sm.id=sml.move_id where sml.lot_id is not null
                and sm.state='done'
                order by sml.lot_id, sm.date desc
            ) as om on om.lot_id=im.lot_id 
            left join (
                -- first move (should always be inbound) 
                select distinct on (spl.name)
                    spl.name as serial_name, sml.lot_id,
                    sml.id as sml_id, sm.date as move_date, sml.location_id, sml.location_dest_id
                from stock_move_line as sml
                left join stock_move sm on sm.id=sml.move_id
                left join stock_lot spl on spl.id=sml.lot_id
                left join product_product pp on pp.id=sml.product_id
                left join product_template pt on pt.id=pp.product_tmpl_id where sml.lot_id is not null
                and sml.state='done'
                and (pt.name ->> 'en_US') not ilike '%generic%'
                order by spl.name, sm.date
            ) as fsm on fsm.serial_name=spl.name
            left join stock_location sl on sl.id=om.location_dest_id left join res_partner rp on rp.id=spl.partner_id
            left join res_partner prp on prp.id=rp.parent_id
            left join (
                -- identify wheel assist builds
                select product_product_id
                    from product_variant_combination pvc
                    left join product_template_attribute_value ptav on ptav.id=pvc.product_template_attribute_value_id
                    where ptav.product_attribute_value_id in (
                        select pav.id
                        from product_attribute_value pav
                        left join product_attribute pa on pa.id=pav.attribute_id where (pa.name ->> 'en_US') like '%wa%'
                    )
                ) as wa on wa.product_product_id=pp.id --where sl.name<>'Production'
            where im.build_date>='2022-01-01' order by spl.name, im.build_date
            )
        """)
