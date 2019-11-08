# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round


class MrpRouting(models.Model):
    _inherit = 'mrp.routing'

    operations_detail = fields.Char(
        string="Operations Detail",
        compute='_compute_operations_detail',
        readonly=True)

    @api.depends('operation_ids')
    def _compute_operations_detail(self):
        for route in self:
            route.operations_detail = ", ".join(route.operation_ids.mapped('workcenter_id.code'))
