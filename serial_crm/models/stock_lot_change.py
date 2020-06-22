from odoo import models, fields, api


class StockLotChange(models.Model):
    _name = 'stock.lot.change'
    _description = 'Serialize Unit Component Changes'
    _order = 'parent_lot_id,change_date'

    parent_lot_id = fields.Many2one(
        comodel_name='stock.production.lot',
        string='Parent Serial',
        required=True)

    change_type = fields.Selection(
        selection=[('add', 'Add'), ('remove', 'Remove'), ('change', 'Change')],
        string='Change Type',
        required=True)

    change_date = fields.Date(
        string='Change Date',
        required=True,
        default=fields.Date.today)

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True)

    bom_qty = fields.Float(
        string='Quantity',
        required=True
    )

    component_lot_id = fields.Many2one(
        comodel_name='stock.production.lot',
        string='Component Serial')
