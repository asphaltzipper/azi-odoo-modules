# -*- coding: utf-8 -*-
# © 2016 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, fields
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)


class MrpMaterialPlan(models.Model):
    _inherit = "mrp.material_plan"

    build_id = fields.Many2one(
        comodel_name='mrp.schedule.line',
        string='MSBuild',
        index=True,
        help='Master Schedule Line item that created this planned order.'
    )

    @api.multi
    def procurement_create(self, proc_name):
        proc_order = super(MrpMaterialPlan, self).procurement_create(proc_name)
        # if the proc_order is in exception, then production_id will be False
        if self.build_id and proc_order.production_id:

            # set the production_id on all current copies of this schedule line
            build_name = self.build_id.name
            sched_lines = self.build_id.search([('name', '=', build_name), ('state', '!=', 'superseded')])
            sched_lines.update({'production_id': proc_order.production_id.id})

            # set serial number on the production_id
            if self.build_id.lot_id:
                # filter move_finished_ids by product_id because there may be byproducts
                # TODO: stock.move.lots record doesn't get created until the user executes Check Availability
                move_lots = proc_order.production_id.move_finished_ids.\
                    filtered(lambda x: x.product_id.id == self.product_id).mapped('move_lot_ids')
                # move_lots.lot_produced_id = self.build_id.lot_id
                pass

        return proc_order

    @api.model
    def load_independent_demand(self):
        super(MrpMaterialPlan, self).load_independent_demand()
        cr = self.env.context.get('use_new_cursor') and self.env.cr

        warehouse = self.env['stock.warehouse'].search([], limit=1)
        location = warehouse.lot_stock_id
        schedule_id = self.env.context.get('schedule_id')
        domain = [('schedule_id.id', '=', schedule_id), ('product_id', '!=', False)]
        scheduled_builds = self.env['mrp.schedule.line'].search(domain)

        if schedule_id:
            message = "Using schedule %s" % self.env['mrp.schedule'].browse(schedule_id).name
            _logger.info(message)
            self.env['mrp.material_plan.log'].create({'type': 'info', 'message': message})

        message = "Creating dependent demand from %s scheduled builds" % len(scheduled_builds)
        _logger.info(message)
        self.env['mrp.material_plan.log'].create({'type': 'info', 'message': message})
        if cr:
            cr.commit()

        for build in scheduled_builds:
            # create independent demand
            vals = self._prepare_planned_order(
                build.product_id,
                1,
                self._get_bucket_from_date(build.date_finish),
                location,
                origin=build.name
            )
            vals['build_id'] = build.id
            new_order = self.create(vals)
            # create dependent demand
            new_order._create_dependent_demand()
            if cr:
                cr.commit()

    def _get_planning_horizon(self):
        last_bucket_date = super(MrpMaterialPlan, self)._get_planning_horizon()

        # check for a later schedule date
        schedule_domain = [('schedule_id.state', '=', 'released'), ('product_id', '!=', False)]
        last_build = self.env['mrp.schedule.line'].search(schedule_domain, order="date_finish DESC", limit=1)
        last_build_date = last_build and datetime.strptime(last_build.date_finish, DEFAULT_SERVER_DATE_FORMAT).date()
        if last_build and last_build_date > last_bucket_date:
            last_bucket_date = self._get_bucket_from_date(last_build.date_finish)

        return last_bucket_date

    def _cron_plan_compute(self):
        ctx = dict(self.env.context)
        schedule = self.env['mrp.schedule'].get_released()
        if schedule:
            ctx['schedule_id'] = schedule.id
        return super(MrpMaterialPlan, self.with_context(ctx))._cron_plan_compute()
