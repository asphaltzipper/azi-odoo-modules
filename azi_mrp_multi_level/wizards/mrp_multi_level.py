from datetime import date
import time
import threading

from odoo import api, fields, models, exceptions, _

import logging
logger = logging.getLogger(__name__)


class MultiLevelMrp(models.TransientModel):
    _inherit = 'mrp.multi.level'

    @api.model
    def _init_mrp_move_from_forecast(self, product_mrp_area):
        super(MultiLevelMrp, self)._init_mrp_move_from_forecast(product_mrp_area)
        requests = self.env['stock.request'].search([
            ('product_id', '=', product_mrp_area.product_id.id),
            ('state', '=', 'submitted'),
            ('scheduled', '=', True),
            ('allocation_ids', '=', False),
            ('sold', '=', False),
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
    def _get_products_missing_pma(self):
        pmas = self.env['product.mrp.area'].search([])
        pma_prod_ids = pmas.mapped('product_id').ids
        domain = [
            ('id', 'not in', pma_prod_ids),
            ('type', '=', 'product'),
            ('eng_management', '=', True),
        ]
        return self.env['product.product'].search(domain)

    def process_mrp(self):
        with api.Environment.manage():
            new_cr = self.pool.cursor()
            self = self.with_env(self.env(cr=new_cr))
            self.run_mrp_multi_level()
            new_cr.close()
            return {}

    def run_mrp_multi_level_in_bg(self):
        threaded_calculation = threading.Thread(target=self.process_mrp, args=())
        threaded_calculation.start()
        return {'type': 'ir.actions.act_window_close'}