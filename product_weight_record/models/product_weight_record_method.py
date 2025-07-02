from odoo import models, fields

class ProductWeightRecordMethod(models.Model):
    _name = 'product.weight.record.method'
    _description = 'Weighing Method'

    name = fields.Char(
        string='Name',
        required=True,
    )
