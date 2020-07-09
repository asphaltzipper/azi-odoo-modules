from datetime import date
import time

from odoo import api, fields, models, exceptions, _

import logging
logger = logging.getLogger(__name__)


class MultiLevelMrp(models.TransientModel):
    _inherit = 'mrp.multi.level'

    @api.model
    def _mrp_calculation(self, mrp_lowest_llc, mrp_areas):
        message = 'Start MRP calculation'
        logger.info(message)
        self.env['material.plan.log'].create({'type': 'info', 'message': message})
        product_mrp_area_obj = self.env['product.mrp.area']
        counter = 0
        if not mrp_areas:
            mrp_areas = self.env['mrp.area'].search([])
        for mrp_area in mrp_areas:
            llc = 0
            while mrp_lowest_llc > llc:
                product_mrp_areas = product_mrp_area_obj.search(
                    [('product_id.llc', '=', llc),
                     ('mrp_area_id', '=', mrp_area.id)])
                llc += 1

                for product_mrp_area in product_mrp_areas:
                    nbr_create = 0
                    onhand = product_mrp_area.qty_available
                    if product_mrp_area.mrp_nbr_days == 0:
                        for move in product_mrp_area.mrp_move_ids:
                            if self._exclude_move(move):
                                continue
                            qtytoorder = product_mrp_area.mrp_minimum_stock - \
                                onhand - move.mrp_qty
                            if qtytoorder > 0.0:
                                cm = self.create_action(
                                    product_mrp_area_id=product_mrp_area,
                                    mrp_date=move.mrp_date,
                                    mrp_qty=qtytoorder, name=move.name)
                                qty_ordered = cm['qty_ordered']
                                onhand += move.mrp_qty + qty_ordered
                                nbr_create += 1
                            else:
                                onhand += move.mrp_qty
                    else:
                        nbr_create = self._init_mrp_move_grouped_demand(
                            nbr_create, product_mrp_area)

                    if onhand < product_mrp_area.mrp_minimum_stock and \
                            nbr_create == 0:
                        qtytoorder = \
                            product_mrp_area.mrp_minimum_stock - onhand
                        cm = self.create_action(
                            product_mrp_area_id=product_mrp_area,
                            mrp_date=date.today(),
                            mrp_qty=qtytoorder,
                            name='Minimum Stock')
                        qty_ordered = cm['qty_ordered']
                        onhand += qty_ordered
                    counter += 1

            log_msg = 'MRP Calculation LLC %s Finished - Nbr. products: %s' % (
                llc - 1, counter)
            logger.info(log_msg)
            self.env['material.plan.log'].create({'type': 'info', 'message': log_msg})

        message = 'End MRP calculation'
        logger.info(message)
        self.env['material.plan.log'].create({'type': 'info', 'message': message})

    @api.multi
    def run_mrp_multi_level(self):
        exec_start = time.time()
        self._mrp_cleanup(self.mrp_area_ids)
        mrp_lowest_llc = self._low_level_code_calculation()
        self._calculate_mrp_applicable(self.mrp_area_ids)
        self._mrp_initialisation(self.mrp_area_ids)
        self._mrp_calculation(mrp_lowest_llc, self.mrp_area_ids)
        self._mrp_final_process(self.mrp_area_ids)
        # Open MRP inventory screen to show result if manually run:
        action = self.env.ref("mrp_multi_level.mrp_inventory_action")
        result = action.read()[0]
        exec_stop = time.time()
        message = "plan complete with execution time=%0.1f minutes" % (
                (exec_stop - exec_start) / 60)
        self.env.user.notify_warning(message=message, title="MRP Complete", sticky=True)
        logger.info(message)
        return result


