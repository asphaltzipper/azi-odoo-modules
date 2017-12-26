# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def action_material_analysis(self):
        self.ensure_one()
        if len(self.product_variant_ids) > 1:
            raise UserError(_("This product has variants.  Choose a variant to analyze."))
        wiz = self.env['mrp.material.analysis'].create({'product_id': self.product_variant_ids.ids[0]})
        return wiz.action_compute()


class ProductProduct(models.Model):
    _inherit = "product.product"

    def action_material_analysis(self):
        self.ensure_one()
        wiz = self.env['mrp.material.analysis'].create({'product_id': self.id})
        return wiz.action_compute()
