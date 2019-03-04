# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_manager = fields.Many2one('res.users', 'Product Manager')


class ProductAttributevalue(models.Model):
    _inherit = "product.attribute.value"

    @api.multi
    def _variant_name(self, variable_attributes):
        return ", ".join(["%s: %s" % (v.attribute_id.name, v.name) for v in self.sorted(key=lambda r: r.attribute_id.name) if v.attribute_id in variable_attributes])
