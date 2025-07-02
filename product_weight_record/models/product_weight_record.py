from odoo import models, fields, api

class ProductWeightRecord(models.Model):
    _name = 'product.weight.record'
    _description = 'Product Weight Record'
    _order = 'create_date desc'

    lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Serial Number',
        ondelete='cascade',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        ondelete='cascade',
    )
    weight = fields.Float(
        string='Weight (lbs)',
        required=True,
    )
    accy_ids = fields.Many2many(
        comodel_name='product.weight.record.accy',
        string='Included Accessories',
    )
    method_id = fields.Many2one(
        comodel_name='product.weight.record.method',
        string='Weighing Method',
        required=True,
    )
    note = fields.Text(
        string='Notes',
    )

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        if self.lot_id:
            self.product_id = self.lot_id.product_id
