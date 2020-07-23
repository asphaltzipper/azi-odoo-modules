# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def action_planned_forecast_detail(self):
        self.ensure_one()
        if len(self.product_variant_ids) > 1:
            raise UserError(_("This product has multiple variants.  Choose a"
                              " variant to analyze."))
        return self.product_variant_ids[0].action_planned_forecast_detail()

    def action_forecast_detail(self):
        self.ensure_one()
        if len(self.product_variant_ids) > 1:
            raise UserError(_("This product has multiple variants.  Choose a"
                              " variant to analyze."))
        return self.product_variant_ids[0].action_forecast_detail()


class ProductProduct(models.Model):
    _inherit = "product.product"

    def action_planned_forecast_detail(self):
        self.ensure_one()
        wiz = self.env['stock.forecast.detail.wizard'].create({'product_id': self.id})
        return wiz.action_compute()

    def action_forecast_detail(self):
        self.ensure_one()
        wiz = self.env['stock.forecast.detail.wizard'].create({
            'product_id': self.id,
            'planned': False,
            'quoted': False,
        })
        return wiz.action_compute()
