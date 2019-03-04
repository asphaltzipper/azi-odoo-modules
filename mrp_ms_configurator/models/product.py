# -*- coding: utf-8 -*-

from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    config_name = fields.Char(size=512)

    def get_config_name(self):
        attr_values = self.attribute_value_ids
        return ', '.join(sorted(['%s: %s' % (l.attribute_id.name, l.name) for l in attr_values]))
