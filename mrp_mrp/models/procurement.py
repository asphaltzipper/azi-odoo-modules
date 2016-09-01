# -*- coding: utf-8 -*-
# © 2016 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class ProcurementOrder(models.Model):
    _inherit = "procurement.order"

    # implement an efficient stand-alone mrp algorithm

    # get orderpoints

    # get exploded bom

    # projected on-hand quantity

    # calculate requirements
    @api.model
    def mrp(self):
        pass
        # do something useful
