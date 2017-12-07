# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def action_material_analysis(self):
        self.ensure_one()
        wiz = self.env['mrp.material.analysis'].create({'product_id': self.product_variant_ids.ids[0]})
        return wiz.action_compute()
