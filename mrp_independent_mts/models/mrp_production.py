# -*- coding: utf-8 -*-
# © 2016 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    independent_mts = fields.Boolean(string='Independent MTS', help="Scheduler"
                                     "should use this order as independent"
                                     "demand. This is only effective when the"
                                     "order is in draft state.")

