# -*- coding: utf-8 -*-
# © 2016 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    due_date = fields.Datetime(string='Due Date', help="Inform production"
                               "workers of expected due date for this order")

    # TODO: automatically set a value for due_date

