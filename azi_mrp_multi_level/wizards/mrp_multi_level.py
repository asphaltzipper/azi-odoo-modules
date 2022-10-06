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

    @api.multi
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
                self.env['material.plan.log'].create({'type': 'error', 'message': message})
            self.env.cr.commit()

        # report product templates having multiple BOMs with the same sequence
        tmpl_bom_ambiguity = self._get_tmpl_bom_ambiguity()
        if tmpl_bom_ambiguity:
            for tmpl in tmpl_bom_ambiguity:
                message = "Multiple BOMs for product %s" % tmpl.display_name
                self.env['material.plan.log'].create({'type': 'warning', 'message': message})
            self.env.cr.commit()

        # report unscheduled sale order lines without reserved serial numbers
        sol_not_reserved = self._get_sol_not_reserved()
        if sol_not_reserved:
            for sol in sol_not_reserved:
                message = "Unscheduled and Unreserved: %s [%s] %s" % (
                    sol['so_name'], sol['default_code'], sol['prod_name'])
                self.env['material.plan.log'].create({'type': 'error', 'message': message})
            self.env.cr.commit()

        # report scheduled sale order lines with reserved serial numbers
        sol_sched_reserved = self._get_sol_sched_reserved()
        if sol_sched_reserved:
            for sol in sol_sched_reserved:
                message = "Scheduled and Reserved, Serial %s: %s [%s] %s" % (
                    sol['serial_num'], sol['so_name'], sol['default_code'], sol['prod_name'])
                self.env['material.plan.log'].create({'type': 'error', 'message': message})
            self.env.cr.commit()

        # report scheduled sale order lines with earlier date
        sol_sched_date_early = self._get_sol_sched_date_early()
        if sol_sched_date_early:
            for sol in sol_sched_date_early:
                message = "SO date earlier than schedule date by %s days: %s / %s -- [%s] %s" % (
                    sol['day_diff'], sol['so_name'], sol['sr_name'], sol['default_code'], sol['prod_name'])
                self.env['material.plan.log'].create({'type': 'error', 'message': message})
            self.env.cr.commit()

        # report scheduled sale order lines with later date
        sol_sched_date_late = self._get_sol_sched_date_late()
        if sol_sched_date_late:
            for sol in sol_sched_date_late:
                message = "SO date later than schedule date by %s days: %s / %s -- [%s] %s" % (
                    sol['day_diff'], sol['so_name'], sol['sr_name'], sol['default_code'], sol['prod_name'])
                self.env['material.plan.log'].create({'type': 'warning', 'message': message})
            self.env.cr.commit()

        # report sale order lines with different product from stock request
        sol_diff_prod = self._get_sol_sched_product_diff()
        if sol_diff_prod:
            for sol in sol_diff_prod:
                message = "SO and Schedule products differ: %s / %s -- [%s] %s" % (
                    sol['so_name'], sol['sr_name'], sol['default_code'], sol['prod_name'])
                self.env['material.plan.log'].create({'type': 'error', 'message': message})
            self.env.cr.commit()

        # report scheduled sale order not confirmed
        sol_sched_not_confirmed = self._get_sol_sched_not_confirmed()
        if sol_sched_not_confirmed:
            for sol in sol_sched_not_confirmed:
                message = "SO linked to SR, but not confirmed: %s (%s) -- %s" % (
                    sol['so_name'], sol['so_state'], sol['sr_name'])
                self.env['material.plan.log'].create({'type': 'warning', 'message': message})
            self.env.cr.commit()

        result = super(MultiLevelMrp, self).run_mrp_multi_level()

        exec_stop = time.time()
        message = "Plan complete with execution time=%0.1f minutes" % (
                (exec_stop - exec_start) / 60)
        self.env.user.notify_warning(message=message, title="MRP Complete", sticky=True)
        self.env.cr.commit()
        self.env['material.plan.log'].create({'type': 'info', 'message': message})
        self.env.cr.commit()

        return result

    @api.model
    def explode_action(
            self, product_mrp_area_id, mrp_action_date, name, qty, action
    ):
        if not product_mrp_area_id.product_id.bom_ids:
            log_msg = 'bom not found for product %s' % \
                      product_mrp_area_id.product_id.display_name
            logger.warning(log_msg)
            self.env['material.plan.log'].create({'type': 'error', 'message': log_msg})
            self.env.cr.commit()
        return super(MultiLevelMrp, self).explode_action(
            product_mrp_area_id, mrp_action_date, name, qty, action)

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
    def _get_tmpl_bom_ambiguity(self):
        sql = """
            select product_tmpl_id
            from mrp_bom
            where active=true
            group by product_tmpl_id, sequence
            having count(*)>1
            order by product_tmpl_id
        """
        self.env.cr.execute(sql)
        tmpl_ids = [x[0] for x in self.env.cr.fetchall()]
        return self.env['product.template'].browse(tmpl_ids)

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
        sol_non_resv = [{'so_name': x[0], 'default_code': x[1], 'prod_name': x[2]} for x in self.env.cr.fetchall()]
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
            left join stock_production_lot spl on spl.id=sml.lot_id
            where sol.delivery_remaining_qty>0
            and so.state='sale'
            and pc.name ilike 'FG - %'
            and sml.lot_id is not null
            and sr.id is not null
        """
        self.env.cr.execute(sql)
        sol_sched_resv = [{
                'so_name': x[0], 'default_code': x[1], 'prod_name': x[2], 'serial_num': x[3], 'sr_name': x[4]
            } for x in self.env.cr.fetchall()]
        return sol_sched_resv

    def _get_sol_sched_date_early(self):
        sql = """
            select
                so.name as so_name,
                sr.name as sr_name,
                pp.default_code,
                pt.name as prod_name,
                sm.date_expected::date as so_date,
                sr.expected_date::date as sr_date,
                abs(round((extract(epoch from sm.date_expected::date) / 86400 - extract(epoch from sr.expected_date::date) / 86400)::decimal, 0)) as day_diff
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
            left join stock_production_lot spl on spl.id=sml.lot_id
            where sol.delivery_remaining_qty>0
            and so.state='sale'
            and pc.name ilike 'FG - %'
            and sr.id is not null
            and round((extract(epoch from sm.date_expected::date) / 86400 - extract(epoch from sr.expected_date::date) / 86400)::decimal, 0)<0
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
                sm.date_expected::date as so_date,
                sr.expected_date::date as sr_date,
                abs(round((extract(epoch from sm.date_expected::date) / 86400 - extract(epoch from sr.expected_date::date) / 86400)::decimal, 0)) as day_diff
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
            left join stock_production_lot spl on spl.id=sml.lot_id
            where sol.delivery_remaining_qty>0
            and so.state='sale'
            and pc.name ilike 'FG - %'
            and sr.id is not null
            and round((extract(epoch from sm.date_expected::date) / 86400 - extract(epoch from sr.expected_date::date) / 86400)::decimal, 0)>0
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
        with api.Environment.manage():
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
