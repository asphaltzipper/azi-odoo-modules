from odoo import models, fields, api


class StockLotChange(models.Model):
    _name = 'stock.lot.change'
    _description = 'Serial Unit Component Changes'
    _order = 'parent_lot_id,change_date'

    parent_lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Parent Serial',
        required=True,
    )

    change_type = fields.Selection(
        selection=[
            ('add', 'Add'),
            ('remove', 'Remove'),
            ('change', 'Change'),
        ],
        string='Change Type',
        required=True,
    )

    change_date = fields.Date(
        string='Change Date',
        required=True,
        default=fields.Date.today,
    )

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
    )

    bom_qty = fields.Float(
        string='Quantity',
        required=True,
    )

    component_lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Component Serial')

    has_child = fields.Boolean(
        string='Has Child',
        compute='_compute_has_child',
        store=True,
    )

    @api.depends('component_lot_id.change_ids')
    def _compute_has_child(self):
        for record in self:
            record.has_child = record.component_lot_id.change_ids and True or False

