# -*- coding: utf-8 -*-
# © 2017 Matt Taylor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, fields

import logging
_logger = logging.getLogger(__name__)


class MrpMaterialPlan(models.Model):
    _inherit = "mrp.material_plan"

    e_kanban = fields.Boolean(
        string="E-Kanban",
        related='product_id.e_kanban',
        readonly=True,
        store=True)
