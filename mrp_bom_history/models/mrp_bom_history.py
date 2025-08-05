from odoo import models, api, fields


class MrpBomHistoryLine(models.Model):
    _name = 'mrp.bom.history.line'
    _description = 'BOM History Details'

    production_id = fields.Many2one('mrp.production', 'Manufacturing Order')
    bom_type = fields.Selection([('normal', 'Manufacture this product'), ('phantom', 'Kit')], 'BOM Type')
    bom_id = fields.Many2one('mrp.bom')
    parent_product_id = fields.Many2one('product.product', 'Parent')
    product_id = fields.Many2one('product.product', 'Product')
    product_qty = fields.Float('Quantity')
    product_uom_id = fields.Many2one('uom.uom', 'Product Unit of Measure')
