# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import UserError


class MaterialPlan(models.Model):
    _inherit = "mrp.material_plan"

    def action_material_analysis(self):
        self.ensure_one()
        return self.product_id.action_material_analysis()
