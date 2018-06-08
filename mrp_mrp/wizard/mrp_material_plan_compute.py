# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

#
# MRP Material Plan:
#    - Calculate material requirements and plan orders from orderpoints
#

from odoo import api, fields, models

import threading


class MrpMaterialPlanCompute(models.TransientModel):
    _name = 'mrp.material_plan.compute'
    _description = 'Compute Material Requirements Plan'

    debug = fields.Boolean(
        string="Debug",
        help='Help! Add debug messages to the mrp_material_plan_log table.'
    )

    product_id = fields.Many2one(
        comodel_name='product.product',
        string="Debug Product",
        help="This product will post additional log messages, when encountered in the planning algorithm.")

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
        ctx = dict(self.env.context)
        ctx['debug_mrp'] = self.debug
        ctx['debug_mrp_product_id'] = self.product_id.id
        threaded_calculation = threading.Thread(target=self.with_context(ctx)._material_plan_compute, args=())
        threaded_calculation.start()
        return {'type': 'ir.actions.act_window_close'}
