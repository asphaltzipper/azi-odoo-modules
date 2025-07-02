from odoo import models, fields

class ProductWeightRecordAccy(models.Model):
    _name = 'product.weight.record.accy'
    _description = 'Weight Record Accessory'

    name = fields.Char(
        string='Accessory Name',
        required=True,
    )
