# -*- coding: utf-8 -*-
# © 2016 Matt Taylor - Asphalt Zipper
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    independent_demand = fields.Boolean(string='Independent Demand',
                                        help="When true, Manufacturing Order represents independent demand. "
                                             "This flag will be set if the order was not "
                                             "created from a procurement, or if it is "
                                             "associated with a Sales Order.")
    #independent_demand = fields.Boolean(string='Independent Demand', store=True, readonly=True, compute='_compute_independent_demand',
    #                                    help="When true, Manufacturing Order represents independent demand. "
    #                                         "This flag will be set if the order was not "
    #                                         "created from a procurement, or if it is "
    #                                         "associated with a Sales Order.")
    date_planned_end = fields.Datetime('End Date', required=True, readonly=True, copy=False, help="Planned date of completion for the entire manufacturing order")

    #@api.depends('id')
    #def _compute_independent_demand(self)
    #    proc_obj = self.env["procurement.order"]
    #    procs = proc_obj.search([('production_id', '=', self.id),])
    #    if self.move_prod_id or not procs:
    #        self.independent_demand = True
    #    else:
    #        self.independent_demand = False
