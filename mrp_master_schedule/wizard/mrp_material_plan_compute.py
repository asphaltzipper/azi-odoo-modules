# -*- coding: utf-8 -*-
# Copyright 2016 Scott Saunders
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models

import threading


class MrpMaterialPlanCompute(models.TransientModel):
    _inherit = 'mrp.material_plan.compute'

    def _get_released_schedule(self):
        return self.env['mrp.schedule'].get_released()

    schedule_id = fields.Many2one(
        comodel_name='mrp.schedule',
        string='Schedule',
        required=False,
        default=_get_released_schedule,
        help='Leaving this blank will compute orderpoint demand only.'
    )

    @api.multi
    def material_plan_calculation(self):
        ctx = dict(self.env.context)
        ctx['schedule_id'] = self.schedule_id.id
        ctx['debug_mrp'] = self.debug
        threaded_calculation = threading.Thread(target=self.with_context(ctx)._material_plan_compute, args=())
        threaded_calculation.start()
        return {'type': 'ir.actions.act_window_close'}
