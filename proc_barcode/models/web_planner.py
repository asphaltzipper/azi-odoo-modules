# -*- coding: utf-8 -*-
from openerp import models


class PlannerBarcode(models.Model):

    _inherit = 'web.planner'

    def _get_planner_application(self):
        planner = super(PlannerBarcode, self)._get_planner_application()
        planner.append(['planner_barcode', 'Barcode Planner'])
        return planner

    def _prepare_planner_barcode_data(self):
        return {
            'is_multi_location': self.env.user.has_group('stock.group_locations'),
        }
