# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

#
# MRP Material Plan:
#    - Calculate material requirements and plan orders from orderpoints
#

from odoo import api, models

import threading


class MrpMaterialPlanCompute(models.TransientModel):
    _name = 'mrp.material_plan.compute'
    _description = 'Compute Material Requirements Plan'

    def _material_plan_compute(self):
        with api.Environment.manage():
            # As this function is in a new thread, I need to open a new cursor, because the old one may be closed
            new_cr = self.pool.cursor()
            self = self.with_env(self.env(cr=new_cr))
            self.env['mrp.material_plan']._run_mrp_api(
                use_new_cursor=new_cr.dbname,
                company_id=self.env.user.company_id.id)
            new_cr.close()
            return {}

    @api.multi
    def material_plan_calculation(self):
        threaded_calculation = threading.Thread(target=self._material_plan_compute, args=())
        threaded_calculation.start()
        return {'type': 'ir.actions.act_window_close'}
