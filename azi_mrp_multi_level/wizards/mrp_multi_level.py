from datetime import date
import time
import threading

from odoo import api, fields, models, exceptions, _
from odoo.exceptions import ValidationError

import logging
logger = logging.getLogger(__name__)
RUNTHREAD = False


class MultiLevelMrp(models.TransientModel):
    _inherit = 'mrp.multi.level'

    @api.model
    def _mrp_cleanup(self, mrp_areas):
        message = "Start MRP Cleanup"
        logger.info(message)
        self.env['material.plan.log'].create({'type': 'info', 'message': message})
        self.env.cr.commit()

        if not mrp_areas:
            mrp_areas = self.env['mrp.area'].search([])

        self.env.cr.execute("""
            delete from mrp_move
            where mrp_area_id in %s
        """, (tuple(mrp_areas.ids), ))
        self.env['mrp.move'].invalidate_model()

        self.env.cr.execute("""
            delete from mrp_inventory
            where mrp_area_id in %s
        """, (tuple(mrp_areas.ids), ))
        self.env['mrp.inventory'].invalidate_model()

        self.env.cr.execute("""
            delete from mrp_planned_order
            where mrp_area_id in %s
            and fixed=false
        """, (tuple(mrp_areas.ids), ))
        self.env['mrp.planned.order'].invalidate_model()

        message = "End MRP Cleanup"
        logger.info(message)
        self.env['material.plan.log'].create({'type': 'info', 'message': message})
        self.env.cr.commit()

        return True

    def _bom_loop_check(self):
        logger.info('Start BoM loop check')

        self.env.cr.execute("""
            with recursive default_bom as (
                -- This auxiliary statement is not recursive, but the recursive
                -- keyword must be placed on the first auxiliary statement.
                -- Here, we get the default BOM for each product template
                --   - active
                --   - highest version
                --   - lowest sequence
                select distinct on (product_tmpl_id, product_id) *
                from mrp_bom
                where active=true
                order by product_tmpl_id, product_id, version desc, sequence
            ),
            adjacency as (
                -- Here, we get a parent-child adjacency list using product id.
                -- If only template is specified on mrp.bom, the list is
                -- expanded with all variant BOMs.
                SELECT DISTINCT
                    COALESCE(b.product_id,p.id) AS parent_id,
                    l.product_id AS comp_id
                FROM mrp_bom_line AS l, default_bom AS b, product_product AS p
                WHERE b.product_tmpl_id=p.product_tmpl_id
                AND l.bom_id=b.id
            ),
            stack (parent_id, comp_id, path, looped) as (
                -- This auxiliary statement is recursive, as indicated by
                -- the UNION keyword.
                SELECT
                    a.parent_id,
                    a.comp_id,
                    ARRAY[a.comp_id] as path,
                    false as looped
                FROM adjacency as a
                UNION ALL
                SELECT
                    a.parent_id,
                    a.comp_id,
                    path || a.comp_id as path,
                    a.comp_id = ANY(path) as looped
                FROM stack AS s, adjacency as a
                WHERE a.parent_id=s.comp_id
                AND NOT s.looped
            )
            select
                s.parent_id,
                s.comp_id,
                s.path
            from stack as s
            where s.looped
        """)

        prod_obj = self.env['product.product']
        loop_sets = []
        loop_names = []
        for data in self.env.cr.fetchall():
            if set(data[2]) in loop_sets:
                # keep loops unique, regardless of order
                continue
            loop_sets.append(set(data[2]))
            prod_names = [prod_obj.browse(pid).display_name for pid in data[2]]
            name = " ==>> ".join(prod_names)
            loop_names.append(name)
        if len(loop_names):
            for loop in loop_names:
                logger.error("Found loop in BOM: %s" % loop)
            raise exceptions.UserError(
                _("BoM loops were detected:\n%s" % "\n".join(loop_names)))
        logger.info("End BoM loop check")

    @api.model
    def _low_level_code_calculation(self):
        self._bom_loop_check()
        logger.info('Start low level code calculation')

        self.env.cr.execute("""
            UPDATE product_product SET llc=t.llc
            FROM (
                with recursive default_bom as (
                    -- This auxiliary statement is not recursive, but the recursive
                    -- keyword must be placed on the first auxiliary statement.
                    -- Here, we get the default BOM for each product template
                    --   - active
                    --   - highest version
                    --   - lowest sequence
                    select distinct on (product_tmpl_id, product_id) *
                    from mrp_bom
                    where active=true
                    order by product_tmpl_id, product_id, version desc, sequence
                ),
                j as (
                    -- Here, we get a parent-child adjacency list using product id.
                    -- If only template is specified on mrp.bom, the list is
                    -- expanded with all variant BOMs.
                    SELECT DISTINCT
                        COALESCE(b.product_id,p.id) AS parent_id,
                        l.product_id AS comp_id
                    FROM mrp_bom_line AS l, default_bom AS b, product_product AS p
                    WHERE b.product_tmpl_id=p.product_tmpl_id
                    AND l.bom_id=b.id
                ),
                stack (parent_id, comp_id, path) AS (
                    -- build bom path array using product id
                    SELECT
                        j.parent_id,
                        j.comp_id,
                        ARRAY[j.comp_id]
                    FROM j
                    UNION ALL
                    SELECT
                        j.parent_id,
                        j.comp_id,
                        path || j.comp_id
                    FROM stack AS s, j
                    WHERE j.parent_id=s.comp_id
                )
                -- length of longest path is the llc
                SELECT
                    p.id as product_id,
                    COALESCE(MAX(ARRAY_LENGTH(path, 1)), 0) AS llc
                FROM product_product AS p
                LEFT JOIN stack AS s ON s.comp_id=p.id
                GROUP BY p.id
                ORDER BY llc DESC
            ) AS t
            WHERE product_product.id=t.product_id
        """)
        self.env['product.product'].invalidate_model(fnames=['llc'])

        self.env.cr.execute("SELECT MAX(llc) FROM product_product")
        mrp_lowest_llc = self.env.cr.fetchall()[0][0]
        logger.info("End low level code calculation:  %d levels" % (mrp_lowest_llc, ))
        return mrp_lowest_llc

    @api.model
    def _exclude_from_mrp(self, product, mrp_area):
        res = super(MultiLevelMrp, self)._exclude_from_mrp(product, mrp_area)
        if res and self._context.get('mrp_explosion'):
            log_msg = 'required, but excluded from mrp: %s' % product.display_name
            self.env['material.plan.log'].create({'type': 'warning', 'message': log_msg})
            self.env.cr.commit()
        return res

    @api.model
    def _init_mrp_move_from_forecast(self, product_mrp_area):
        super(MultiLevelMrp, self)._init_mrp_move_from_forecast(product_mrp_area)
        requests = self.env['stock.request'].search([
            ('product_id', '=', product_mrp_area.product_id.id),
            ('state', '=', 'submitted'),
            ('scheduled', '=', True),
        ])
        for request in requests:
            mrp_date = date.today()
            if fields.Date.from_string(request.expected_date) > date.today():
                mrp_date = fields.Date.from_string(request.expected_date)
            self.create_action(
                product_mrp_area,
                mrp_date,
                request.product_uom_qty,
                request.name
            )
            # The _mrp_calculation method doesn't check existing planned orders.
            # Even though we create planned orders for the scheduled builds, the
            # algorithm creates more planned orders to satisfy any real demand.
            # The _mrp_calculation method does check the mrp.move records, so we
            # add an mrp.move record to show the scheduled build as a supply.
            vals = {
                'product_id': request.product_id.id,
                'product_mrp_area_id': product_mrp_area.id,
                'production_id': False,
                'purchase_order_id': False,
                'purchase_line_id': False,
                'stock_move_id': False,
                'mrp_qty': request.product_uom_qty,
                'current_qty': request.product_uom_qty,
                'mrp_date': mrp_date,
                'current_date': mrp_date,
                'mrp_type': 's',
                'mrp_origin': 'fc',
                'mrp_order_number': request.name,
                'parent_product_id': False,
                'name': request.name,
                'state': 'confirmed',
            }
            self.env['mrp.move'].create(vals)

    @api.model
    def _mrp_initialisation(self, mrp_areas):
        message = 'Start MRP initialization'
        self.env['material.plan.log'].create({'type': 'info', 'message': message})
        self.env.cr.commit()

        super(MultiLevelMrp, self)._mrp_initialisation(mrp_areas)

        message = 'End MRP initialization'
        logger.info(message)
        self.env['material.plan.log'].create({'type': 'info', 'message': message})
        self.env.cr.commit()

    @api.model
    def _mrp_final_process(self, mrp_areas):
        message = 'Start MRP finalization'
        self.env['material.plan.log'].create({'type': 'info', 'message': message})
        self.env.cr.commit()

        super(MultiLevelMrp, self)._mrp_final_process(mrp_areas)

        # populate expedite field
        message = 'Marking Expedite Orders'
        self.env['material.plan.log'].create({'type': 'info', 'message': message})
        self.env.cr.commit()
        inv_ids = self._get_expedite_mrp_inv()
        if inv_ids:
            invs = self.env['mrp.inventory'].browse(inv_ids)
            invs.update({'to_expedite': True})

        message = 'End MRP finalization'
        logger.info(message)
        self.env['material.plan.log'].create({'type': 'info', 'message': message})
        self.env.cr.commit()

    @api.model
    def _mrp_calculation(self, mrp_lowest_llc, mrp_areas):
        message = 'Start MRP calculation'
        self.env['material.plan.log'].create({'type': 'info', 'message': message})
        self.env.cr.commit()

        super(MultiLevelMrp, self)._mrp_calculation(mrp_lowest_llc, mrp_areas)

        message = 'End MRP calculation'
        logger.info(message)
        self.env['material.plan.log'].create({'type': 'info', 'message': message})
        self.env.cr.commit()

    def run_mrp_multi_level(self):
        exec_start = time.time()
        message = "MRP run started by user %s" % self.env.user.display_name
        self.env['material.plan.log'].create({'type': 'info', 'message': message})
        self.env.cr.commit()

        # report products with no product_mrp_area record
        no_pma_products = self._get_products_missing_pma()
        if no_pma_products:
            for product in no_pma_products:
                message = "Missing parameters for %s" % product.display_name
                self.env['material.plan.log'].create({
                    'type': 'error',
                    'message': message,
                })
            self.env.cr.commit()

        # report products having multiple BOMs with the same sequence
        default_bom_ambiguity = self._get_default_bom_ambiguity()
        if default_bom_ambiguity:
            for vals in default_bom_ambiguity:
                message = _(
                    "Conflicting default BOMs (%s with sequence=%s) for product %s",
                    vals["bom_count"],
                    vals["min_sequence"],
                    vals["product"].display_name,
                )
                self.env['material.plan.log'].create({
                    'type': 'warning',
                    'message': message,
                })
            self.env.cr.commit()

        # report unscheduled sale order lines without reserved serial numbers
        sol_not_reserved = self._get_sol_not_reserved()
        if sol_not_reserved:
            for sol in sol_not_reserved:
                message = _(
                    "Unscheduled and Unreserved: %s [%s] %s",
                    sol['so_name'],
                    sol['default_code'],
                    sol['prod_name'],
                )
                self.env['material.plan.log'].create({
                    'type': 'error',
                    'message': message,
                })
            self.env.cr.commit()

        # report scheduled sale order lines with reserved serial numbers
        sol_sched_reserved = self._get_sol_sched_reserved()
        if sol_sched_reserved:
            for sol in sol_sched_reserved:
                message = _(
                    "Scheduled and Reserved, Serial %s: %s [%s] %s",
                    sol['serial_num'],
                    sol['so_name'],
                    sol['default_code'],
                    sol['prod_name'],
                )
                self.env['material.plan.log'].create({'type': 'error', 'message': message})
            self.env.cr.commit()

        # report scheduled sale order lines with earlier date
        sol_sched_date_early = self._get_sol_sched_date_early()
        if sol_sched_date_early:
            for sol in sol_sched_date_early:
                message = _(
                    "SO date earlier than schedule date by %s days: %s / %s -- [%s] %s",
                    sol['day_diff'],
                    sol['so_name'],
                    sol['sr_name'],
                    sol['default_code'],
                    sol['prod_name'],
                )
                self.env['material.plan.log'].create({
                    'type': 'error',
                    'message': message,
                })
            self.env.cr.commit()

        # report scheduled sale order lines with later date
        sol_sched_date_late = self._get_sol_sched_date_late()
        if sol_sched_date_late:
            for sol in sol_sched_date_late:
                message = _(
                    "SO date later than schedule date by %s days: %s / %s -- [%s] %s",
                    sol['day_diff'],
                    sol['so_name'],
                    sol['sr_name'],
                    sol['default_code'],
                    sol['prod_name'],
                )
                self.env['material.plan.log'].create({
                    'type': 'warning',
                    'message': message,
                })
            self.env.cr.commit()

        # report sale order lines with different product from stock request
        sol_diff_prod = self._get_sol_sched_product_diff()
        if sol_diff_prod:
            for sol in sol_diff_prod:
                message = _(
                    "SO and Schedule products differ: %s / %s -- [%s] %s",
                    sol['so_name'],
                    sol['sr_name'],
                    sol['default_code'],
                    sol['prod_name'],
                )
                self.env['material.plan.log'].create({
                    'type': 'error',
                    'message': message,
                })
            self.env.cr.commit()

        # report scheduled sale order not confirmed
        sol_sched_not_confirmed = self._get_sol_sched_not_confirmed()
        if sol_sched_not_confirmed:
            for sol in sol_sched_not_confirmed:
                message = _(
                    "SO linked to SR, but not confirmed: %s (%s) -- %s",
                    sol['so_name'],
                    sol['so_state'],
                    sol['sr_name'],
                )
                self.env['material.plan.log'].create({
                    'type': 'warning',
                    'message': message,
                })
            self.env.cr.commit()

        result = super(MultiLevelMrp, self).run_mrp_multi_level()

        exec_stop = time.time()
        message = _(
            "Plan complete with execution time=%0.1f minutes",
            (exec_stop - exec_start) / 60,
        )
        self.env.user.notify_warning(message=message, title="MRP Complete", sticky=True)
        self.env.cr.commit()
        self.env['material.plan.log'].create({'type': 'info', 'message': message})
        self.env.cr.commit()

        return result

    @api.model
    def explode_action(
        self, product_mrp_area_id, mrp_action_date, name, qty, action, values=None
    ):
        if not product_mrp_area_id.product_id.bom_ids:
            log_msg = 'bom not found for product %s' % \
                      product_mrp_area_id.product_id.display_name
            logger.warning(log_msg)
            self.env['material.plan.log'].create({'type': 'error', 'message': log_msg})
            self.env.cr.commit()
        return super(MultiLevelMrp, self).explode_action(
            product_mrp_area_id, mrp_action_date, name, qty, action, values)

    @api.model
    def _get_products_missing_pma(self):
        pmas = self.env['product.mrp.area'].search([])
        pma_prod_ids = pmas.mapped('product_id').ids
        domain = [
            ('id', 'not in', pma_prod_ids),
            ('type', '=', 'product'),
            ('eng_management', '=', True),
        ]
        return self.env['product.product'].search(domain)

    @api.model
    def _get_default_bom_ambiguity(self):
        sql = """
            with min_sequence as (
                -- minimum sequence among variant boms and template only boms for 
                -- each product variant
                select
                    pp.id as product_id,
                    min(mb.sequence) as min_sequence
                from product_product pp
                left join mrp_bom mb on mb.product_tmpl_id=pp.product_tmpl_id
                where pp.active=true
                and mb.active=true
                and (mb.product_id=pp.id or mb.product_id is null)
                group by pp.id
            )
            select
                product_id,
                min_sequence,
                count(*) as bom_count
            from (
                -- variant boms matching minimum sequence
                select
                    vms.product_id,
                    vms.min_sequence,
                    mb.id as bom_id
                from min_sequence vms
                left join product_product pp on pp.id=vms.product_id
                left join mrp_bom mb
                    on mb.product_id=vms.product_id
                    and mb.sequence=vms.min_sequence
                where mb.active=true
                union
                -- template only boms matching minimum sequence
                select
                    vms.product_id,
                    vms.min_sequence,
                    mb.id as bom_id
                from min_sequence vms
                left join product_product pp on pp.id=vms.product_id
                left join mrp_bom mb
                    on mb.product_tmpl_id=pp.product_tmpl_id
                    and mb.sequence=vms.min_sequence
                where mb.active=true
                and mb.product_id is null
            ) as t
            group by t.product_id, t.min_sequence
            having count(*)>1
        """
        self.env.cr.execute(sql)
        vals = [
            {
                "product": self.env['product.product'].browse(x[0]),
                "min_sequence": x[1],
                "bom_count": x[2],
            }
            for x in self.env.cr.fetchall()
        ]
        return vals

    def _get_sol_not_reserved(self):
        sql = """
            select
                so.name as so_name,
                pp.default_code,
                pt.name as prod_name
            from sale_order_line sol
            left join sale_order so on so.id=sol.order_id
            left join product_product pp on pp.id=sol.product_id
            left join product_template pt on pt.id=pp.product_tmpl_id
            left join product_category pc on pc.id=pt.categ_id
            left join (
                select *
                from stock_request
                where state in ('submitted', 'draft', 'open')
            ) sr on sr.sale_order_line_id=sol.id
            left join (
                select *
                from stock_move
                where state not in ('cancel')
            ) sm on sm.sale_line_id=sol.id
            left join stock_move_line sml on sml.move_id=sm.id
            where sol.delivery_remaining_qty>0
            and so.state='sale'
            and pc.name ilike 'FG - %'
            and sml.lot_id is null
            and sr.id is null
        """
        self.env.cr.execute(sql)
        sol_non_resv = [
            {
                'so_name': x[0],
                'default_code': x[1],
                'prod_name': x[2]
            }
            for x in self.env.cr.fetchall()
        ]
        return sol_non_resv

    def _get_sol_sched_reserved(self):
        sql = """
            select
                so.name as so_name,
                pp.default_code,
                pt.name as prod_name,
                spl.name as serial_num,
                sr.name as sr_name
            from sale_order_line sol
            left join sale_order so on so.id=sol.order_id
            left join product_product pp on pp.id=sol.product_id
            left join product_template pt on pt.id=pp.product_tmpl_id
            left join product_category pc on pc.id=pt.categ_id
            left join (
                select *
                from stock_request
                where state in ('submitted', 'draft', 'open')
            ) sr on sr.sale_order_line_id=sol.id
            left join (
                select *
                from stock_move
                where state not in ('cancel')
            ) sm on sm.sale_line_id=sol.id
            left join stock_move_line sml on sml.move_id=sm.id
            left join stock_lot spl on spl.id=sml.lot_id
            where sol.delivery_remaining_qty>0
            and so.state='sale'
            and pc.name ilike 'FG - %'
            and sml.lot_id is not null
            and sr.id is not null
        """
        self.env.cr.execute(sql)
        sol_sched_resv = [
            {
                'so_name': x[0],
                'default_code': x[1],
                'prod_name': x[2],
                'serial_num': x[3],
                'sr_name': x[4],
            }
            for x in self.env.cr.fetchall()
        ]
        return sol_sched_resv

    def _get_sol_sched_date_early(self):
        sql = """
            select
                so.name as so_name,
                sr.name as sr_name,
                pp.default_code,
                pt.name as prod_name,
                sm.date_deadline::date as so_date,
                sr.expected_date::date as sr_date,
                abs(round((extract(epoch from sm.date_deadline::date) / 86400 - extract(epoch from sr.expected_date::date) / 86400)::decimal, 0)) as day_diff
            from sale_order_line sol
            left join sale_order so on so.id=sol.order_id
            left join product_product pp on pp.id=sol.product_id
            left join product_template pt on pt.id=pp.product_tmpl_id
            left join product_category pc on pc.id=pt.categ_id
            left join (
                select *
                from stock_request
                where state in ('submitted', 'draft', 'open')
            ) sr on sr.sale_order_line_id=sol.id
            left join (
                select *
                from stock_move
                where state not in ('cancel')
            ) sm on sm.sale_line_id=sol.id
            left join stock_move_line sml on sml.move_id=sm.id
            left join stock_lot spl on spl.id=sml.lot_id
            where sol.delivery_remaining_qty>0
            and so.state='sale'
            and pc.name ilike 'FG - %'
            and sr.id is not null
            and round((extract(epoch from sm.date_deadline::date) / 86400 - extract(epoch from sr.expected_date::date) / 86400)::decimal, 0)<0
        """
        self.env.cr.execute(sql)
        sol_sched_diff = [{
                'so_name': x[0],
                'sr_name': x[1],
                'default_code': x[2],
                'prod_name': x[3],
                'so_date': x[4],
                'sr_date': x[5],
                'day_diff': x[6],
            } for x in self.env.cr.fetchall()]
        return sol_sched_diff

    def _get_sol_sched_date_late(self):
        sql = """
            select
                so.name as so_name,
                sr.name as sr_name,
                pp.default_code,
                pt.name as prod_name,
                sm.date_deadline::date as so_date,
                sr.expected_date::date as sr_date,
                abs(round((extract(epoch from sm.date_deadline::date) / 86400 - extract(epoch from sr.expected_date::date) / 86400)::decimal, 0)) as day_diff
            from sale_order_line sol
            left join sale_order so on so.id=sol.order_id
            left join product_product pp on pp.id=sol.product_id
            left join product_template pt on pt.id=pp.product_tmpl_id
            left join product_category pc on pc.id=pt.categ_id
            left join (
                select *
                from stock_request
                where state in ('submitted', 'draft', 'open')
            ) sr on sr.sale_order_line_id=sol.id
            left join (
                select *
                from stock_move
                where state not in ('cancel')
            ) sm on sm.sale_line_id=sol.id
            left join stock_move_line sml on sml.move_id=sm.id
            left join stock_lot spl on spl.id=sml.lot_id
            where sol.delivery_remaining_qty>0
            and so.state='sale'
            and pc.name ilike 'FG - %'
            and sr.id is not null
            and round((extract(epoch from sm.date_deadline::date) / 86400 - extract(epoch from sr.expected_date::date) / 86400)::decimal, 0)>0
        """
        self.env.cr.execute(sql)
        sol_sched_diff = [{
                'so_name': x[0],
                'sr_name': x[1],
                'default_code': x[2],
                'prod_name': x[3],
                'so_date': x[4],
                'sr_date': x[5],
                'day_diff': x[6],
            } for x in self.env.cr.fetchall()]
        return sol_sched_diff

    def _get_sol_sched_product_diff(self):
        sql = """
            select
                so.name as so_name,
                pp.default_code,
                pt.name as prod_name,
                sr.name as sr_name
            from sale_order_line sol
            left join sale_order so on so.id=sol.order_id
            left join product_product pp on pp.id=sol.product_id
            left join product_template pt on pt.id=pp.product_tmpl_id
            left join product_category pc on pc.id=pt.categ_id
            left join (
                select *
                from stock_request
                where state in ('submitted', 'draft', 'open')
            ) sr on sr.sale_order_line_id=sol.id
            left join (
                select *
                from stock_move
                where state not in ('cancel')
            ) sm on sm.sale_line_id=sol.id
            left join stock_move_line sml on sml.move_id=sm.id
            where sol.delivery_remaining_qty>0
            and so.state='sale'
            and pc.name ilike 'FG - %'
            and sr.id is not null
            and sol.product_id<>sr.product_id
        """
        self.env.cr.execute(sql)
        sol_diff_prod = [
            {'so_name': x[0], 'default_code': x[1], 'prod_name': x[2], 'sr_name': x[3]}
            for x in self.env.cr.fetchall()
        ]
        return sol_diff_prod

    def _get_sol_sched_not_confirmed(self):
        sql = """
            select
                so.name as so_name,
                so.state as so_state,
                sr.name as sr_name
            from sale_order_line sol
            left join sale_order so on so.id=sol.order_id
            left join product_product pp on pp.id=sol.product_id
            left join product_template pt on pt.id=pp.product_tmpl_id left join product_category pc on pc.id=pt.categ_id
            left join (
                select *
                from stock_request
                where state in ('submitted', 'draft', 'open')
            ) sr on sr.sale_order_line_id=sol.id
            where so.state<>'sale'
            and pc.name ilike 'FG - %'
            and sr.id is not null
        """
        self.env.cr.execute(sql)
        sol_diff_prod = [
            {'so_name': x[0], 'so_state': x[1], 'sr_name': x[2]}
            for x in self.env.cr.fetchall()
        ]
        return sol_diff_prod

    def _get_expedite_mrp_inv(self):
        sql = """
            select
                mi.id as mrp_inv_id
            from mrp_inventory as mi
            left join (
                -- real orders
                select distinct on (mi.product_mrp_area_id)
                    mi.product_mrp_area_id,
                    mi.date
                from mrp_inventory mi
                where mi.supply_qty<>0
                order by mi.product_mrp_area_id, mi.date desc
            ) as ro on ro.product_mrp_area_id=mi.product_mrp_area_id
            where mi.to_procure<>0
            and mi.order_release_date<ro.date
        """
        self.env.cr.execute(sql)
        return [x[0] for x in self.env.cr.fetchall()]

    def process_mrp(self):
        new_cr = self.pool.cursor()
        self = self.with_env(self.env(cr=new_cr))
        self.run_mrp_multi_level()
        new_cr.close()
        global RUNTHREAD
        RUNTHREAD = False
        return {}

    def run_mrp_multi_level_in_bg(self):
        global RUNTHREAD
        if not RUNTHREAD:
            RUNTHREAD = True
            threaded_calculation = threading.Thread(target=self.process_mrp, args=())
            threaded_calculation.start()
        else:
            raise ValidationError(_('It is already running in the background'))
        return {'type': 'ir.actions.act_window_close'}
