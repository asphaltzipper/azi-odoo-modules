# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import UserError

import json


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    proc_date = fields.Date('Date')

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_qty = fields.Float(related='product_variant_ids.product_qty')

class ProductProduct(models.Model):
    _inherit = 'product.product'

    product_qty = fields.Float(string='Quantity')